from server import app
from flask import render_template, Response
import mediapipe as mp
import cv2
import time
import posture
import beepy

def generate_frames():
    previous_time = 0
    # creating our model to draw landmarks
    mpDraw = mp.solutions.drawing_utils
    # creating our model to detected our pose
    my_pose = mp.solutions.pose
    pose = my_pose.Pose()
    
    font = cv2.FONT_HERSHEY_PLAIN

    Posture = None
    
    set_height = True
    height_count = 0
    temp_height = 0
    cap = cv2.VideoCapture(0)
    loop_count = 0
    num_iterations = 10

    while True:

        success, img = cap.read()
        # converting image to RGB from BGR cuz mediapipe only work on RGB
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = pose.process(imgRGB)
        # print(result.pose_landmarks)
        if result.pose_landmarks:
            mpDraw.draw_landmarks(img, result.pose_landmarks, my_pose.POSE_CONNECTIONS)

        lm = result.pose_landmarks
        height = int(lm.landmark[0].y * 100) if lm else 0

        if set_height:
            text = 'Calibrating'
            # get boundary of this text
            textsize = cv2.getTextSize(text, font, 3, 3)[0]
            # get coords based on boundary
            textX = (img.shape[1] - textsize[0]) // 2

            cv2.putText(img, text, (textX, 50), font, 3, (255, 0, 0), 3)
            temp_height += height
            height_count += 1
            if height_count == 100:
                set_height = False
                Posture = posture.Posture(temp_height / 100)
        
        if not set_height:
            Posture.new_val(height)

            if (Posture.is_slouch()):
                text = 'Sit up straight.'
                # get boundary of this text
                textsize = cv2.getTextSize(text, font, 3, 3)[0]
                # get coords based on boundary
                textX = (img.shape[1] - textsize[0]) // 2
                
                cv2.putText(img, text, (textX, 50), font, 3, (0, 0, 255), 3)
                if loop_count == 1:
                    beepy.beep(sound="error")
            else:
                text = "You're doing great!"
                # get boundary of this text
                textsize = cv2.getTextSize(text, font, 3, 3)[0]
                # get coords based on boundary
                textX = (img.shape[1] - textsize[0]) // 2

                cv2.putText(img, text, (textX, 50), font, 3, (0, 255, 0), 3)
                    
        frame = cv2.imencode('.jpg', img)[1].tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        key = cv2.waitKey(20)
        if key == 27:
            break
            
        loop_count += 1
        loop_count = loop_count % num_iterations

@app.route('/')
def index():
    return render_template('index.js')

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
