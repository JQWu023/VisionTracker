import cv2
import dlib
from eye import Eye
from calibration import Calibration
import numpy as np
from scipy.spatial import distance as dist 
import time

class EyeTracking(object):
    """
    This class tracks the user's gaze.
    It provides useful information like the position of the eyes
    and pupils and allows to know if the eyes are open or closed
    """

    def __init__(self):
        self.frame = None
        self.eye_left = None
        self.eye_right = None
        self.shape_68 = None
        self.COUNTER = 0
        self.TOTAL = 0
        #(Constant value) Eye blink threshold value
        self.EYE_AR_THRESH = 0.196
        #Constant value to indicate three consecutive frames with EAR less than the threshold must happen
        self.EYE_AR_CONSEC_FRAMES = 3
        self.tic = time.perf_counter()
        self.tem_total = 0
        self.blinking = None
        self.calibration = Calibration()

        # _face_detector is used to detect faces
        self.face_detector = dlib.get_frontal_face_detector()

        # _predictor is used to get facial landmarks of a given face
        
        self._predictor = dlib.shape_predictor('shape_68.dat')

    @property
    def pupils_located(self):
        """Check that the pupils have been located"""
        try:
            int(self.eye_left.pupil.x)
            int(self.eye_left.pupil.y)
            int(self.eye_right.pupil.x)
            int(self.eye_right.pupil.y)
            return True
        except Exception:
            return False

    def detector(self):
        """Detects the face and initialize Eye objects"""
        frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        faceRect = self.face_detector(frame)
        if(len(faceRect)<1):
            cv2.putText(self.frame,"No face found. Make sure you are facing the camera",(int(self.frame.shape[0]/8),int(self.frame.shape[1]/1.5)),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,0,255),1)
        try:
            landmarks = self._predictor(frame, faceRect[0])
            self.shape_68 = self.shape_to_np(landmarks)
            self.eye_left = Eye(frame, landmarks, 0, self.calibration,self.shape_68)
            self.eye_right = Eye(frame, landmarks, 1, self.calibration,self.shape_68)
            self.blinking = self.blinkingDetector()
            self.AvgBlinking()
        except IndexError:
            self.eye_left = None
            self.eye_right = None
    def shape_to_np(self,shape, dtype="int"):
        #Initialized
        coords = np.zeros((68, 2), dtype=dtype)

        #Loop for 68 to specify the coordinates of the keypoints
        for i in range(0, 68):
            #Convert to tuples of (x,y)
            coords[i] = (shape.part(i).x, shape.part(i).y)
        return coords
        # Loop through all the points
        # for n in range(0, 68):
        #     x = landmarks.part(n).x
        #     y = landmarks.part(n).y

        #     # Draw a circle
        #     cv2.circle(img=img, center=(x, y), radius=3, color=(0, 255, 0), thickness=-1)
    def refresh(self, frame):
        """Refreshes the frame and analyzes it.

        Arguments:
            frame (numpy.ndarray): The frame to analyze
        """
        self.frame = frame
        self.detector()

    def pupil_left_coords(self):
        """Returns the coordinates of the left pupil"""
        if self.pupils_located:
            x = self.eye_left.origin[0] + self.eye_left.pupil.x
            y = self.eye_left.origin[1] + self.eye_left.pupil.y
            return (x, y)

    def pupil_right_coords(self):
        """Returns the coordinates of the right pupil"""
        if self.pupils_located:
            x = self.eye_right.origin[0] + self.eye_right.pupil.x
            y = self.eye_right.origin[1] + self.eye_right.pupil.y
            return (x, y)

    def horizontal_ratio(self):
        """Returns a number between 0.0 and 1.0 that indicates the
        horizontal direction of the gaze. The extreme right is 0.0,
        the center is 0.5 and the extreme left is 1.0
        """
        if self.pupils_located:
            pupil_left = self.eye_left.pupil.x / (self.eye_left.center[0] * 2 - 10)
            pupil_right = self.eye_right.pupil.x / (self.eye_right.center[0] * 2 - 10)
            return (pupil_left + pupil_right) / 2

    def vertical_ratio(self):
        """Returns a number between 0.0 and 1.0 that indicates the
        vertical direction of the gaze. The extreme top is 0.0,
        the center is 0.5 and the extreme bottom is 1.0
        """
        if self.pupils_located:
            pupil_left = self.eye_left.pupil.y / (self.eye_left.center[1] * 2 - 10)
            pupil_right = self.eye_right.pupil.y / (self.eye_right.center[1] * 2 - 10)       
            return (pupil_left + pupil_right) / 2

    def is_right(self):
        """Returns true if the user is looking to the right"""
        if self.pupils_located:
            return self.horizontal_ratio() > 0.748

    def is_left(self):
        """Returns true if the user is looking to the left"""
        if self.pupils_located:
            return self.horizontal_ratio() < 0.565

    def is_center(self):
        """Returns true if the user is looking to the center"""
        if self.pupils_located:
            return self.is_right() is not True and self.is_left() is not True
    def is_top(self):
        if self.pupils_located:
            return self.vertical_ratio() < 0.6
    def is_bot(self):
        if self.pupils_located:
            return self.vertical_ratio() > 0.98

    def eye_aspect_ratio(self,eye):
        # compute the euclidean distances between the two sets of
        # vertical eye landmarks (x, y)-coordinates
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        # compute the euclidean distance between the horizontal
        # eye landmark (x, y)-coordinates
        C = dist.euclidean(eye[0], eye[3])
        # compute the eye aspect ratio
        ear = (A + B) / (2.0 * C)
        # return the eye aspect ratio
        return ear
    
    def eyeBlinking(self):
        leftEAR = self.eye_aspect_ratio(self.shape_68[42:48]) #left
        rightEAR = self.eye_aspect_ratio(self.shape_68[36:42]) # right
        #average the EAR together for both eyes
        EAR = (leftEAR+rightEAR)/2.0
        return EAR
    
    def blinkingDetector(self):
        # check to see if the eye aspect ratio is below the blink threshold, and if so, increment the blink frame counter
        EAR = self.eyeBlinking()
        #print("EAR: "+str(EAR))
        if EAR > self.EYE_AR_THRESH:
            self.COUNTER += 1
            return False
        # otherwise, the eye aspect ratio is not below the blink threshold
        else:
            # if the eyes were closed for a sufficient number of
            # then increment the total number of blinks
            if self.COUNTER >= self.EYE_AR_CONSEC_FRAMES:
                self.TOTAL += 1
                self.tem_total += 1
                print("Blinked")
                toc = time.perf_counter()
                elapsed_time = toc - self.tic
                # self.y.append(int(elapsed_time))
                # self.x.append(self.tem_total)
                self.COUNTER = 0
                return True
            # reset the eye frame counter
            self.COUNTER = 0
            return False

    def AvgBlinking(self):
        EAR = self.eyeBlinking()
        toc = time.perf_counter()
        elapsed_time = toc - self.tic
        if(elapsed_time>60):
            self.tic = time.perf_counter()
            self.tem_total = 0
            elapsed_time = 0
                    
    def annotated_frame(self):
        """Returns the main frame with pupils highlighted"""
        frame = self.frame.copy()

        if self.pupils_located:
            color = (0, 0, 255)
            x_left, y_left = self.pupil_left_coords()
            x_right, y_right = self.pupil_right_coords()
            cv2.circle(frame, (x_left, y_left), 3, (0, 0, 255), -1)
            cv2.circle(frame, (x_right, y_right), 3, (0, 0, 255), -1)

        return frame
