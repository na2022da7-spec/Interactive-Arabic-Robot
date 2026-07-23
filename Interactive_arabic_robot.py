import speech_recognition as sr
from gtts import gTTS
import pygame
import os
from google import genai
from cvzone.SerialModule import SerialObject
from time import sleep



# Initializations

#  (Arduino)
try:
    arduino = SerialObject(digits=3)
    last_positions = [180, 0, 90]  # LServo, RServo, HServo
except Exception as e:
    print(f"الاردوينو غير متصل: {e}")
    arduino = None

# (Gemini)
MY_API_KEY = ""
client = genai.Client(api_key=MY_API_KEY)

# تهيئة تشغيل الصوت
pygame.mixer.init()


# Functions

def text_to_speech_google(text):
    """تحويل النص إلى صوت باستخدام Google TTS"""
    print(f" نبراس: {text}")
    try:
        # إنشاء ملف صوتي مؤقت باللغة العربية
        tts = gTTS(text=text, lang='ar', slow=False)
        filename = "temp_voice.mp3"
        tts.save(filename)

        # تشغيل الملف
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        # إغلاق الملف وحذفه لتجنب مشاكل الذاكرة
        pygame.mixer.music.unload()
        os.remove(filename)
    except Exception as e:
        print(f"خطأ في النطق: {e}")


def play_sound(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(5)


def play_sound_async(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        # حركة 1
        move_servo([130, 130, 110])
        # حركة 2
        move_servo([30, 30, 50])


def listen_with_google():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
            print("استماع..")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            play_sound("Recources/listen.mp3")

            audio = recognizer.listen(source)

            play_sound("Recources/convert.mp3")

            try:
                text = recognizer.recognize_google(audio, language='ar-SA')
                print("أنت قلت: " + text)
                return text

            except sr.UnknownValueError:
                text = "ءاسف بس مافهمت وش تقول"
                confused_movement()
                text_to_speech_google(text)
                print(text)
                return ""

            except sr.RequestError as e:
                text = "مشكلة في الاتصال"
                print(text, e)
                return ""

            except Exception as e:
                captured_text = input("اكتب ماتريد: ")
                return captured_text


def move_servo(target_positions, delay=0.001):
    global last_positions
    if arduino is None: return

    max_steps = max(abs(target_positions[i] - last_positions[i]) for i in range(3))
    if max_steps == 0: return

    for step in range(max_steps):
        current_positions = [
            last_positions[i] + (step + 1) * (target_positions[i] - last_positions[i]) // max_steps
            for i in range(3)
        ]
        arduino.sendData(current_positions)
        sleep(delay)
    last_positions = target_positions[:]


def hello_gesture():
    """حركة الترحيب"""
    print("تفعيل حركة الترحيب...")
    global last_positions
    move_servo([last_positions[0], 150, last_positions[2]])
    for _ in range(3):
        move_servo([last_positions[0], 130, last_positions[2]])
        move_servo([last_positions[0], 150, last_positions[2]])
    move_servo([last_positions[0], 0, last_positions[2]])


def dance_and_sing_gesture():
    """الرقص والغناء في وقت واحد"""
    print("نبراس يغني ويرقص.. عاشوا!")
    # 1. ابدأ تشغيل الأغنية في الخلفية
    play_sound_async("Recources/song.mpeg")
    # 3. العودة لوضعية الاستعداد بعد انتهاء الأغنية
    move_servo([180, 0, 90])
def confused_movement():
        global last_positions
        center = last_positions[2]
        move_servo([last_positions[0], last_positions[1], center + 25])
        move_servo([last_positions[0], last_positions[1], center - 25])

        move_servo([last_positions[0], last_positions[1], center + 20])
        move_servo([last_positions[0], last_positions[1], center - 20])

        move_servo([last_positions[0], last_positions[1], center])


def talking_movement():
    global last_positions
    L_hand = last_positions[0]
    R_hand = last_positions[1]

    for h in range(2):
        move_servo([L_hand + 10, R_hand - 10, last_positions[2]])
        move_servo([L_hand - 10, R_hand + 10, last_positions[2]])

    move_servo([L_hand, R_hand, last_positions[2]])

# ------------------- Main Loop -------------------

if __name__ == "__main__":
        print("--- روبوت نبراس (النسخة العربية) جاهز ---")

        while True:
            # وضعية الاستعداد
            move_servo([180, 0, 90], delay=0.001)

            # 1. الاستماع
            captured_text = listen_with_google()

            if captured_text.strip():
                # 2. التحقق من الترحيب (بالعربية)
                if any(word in captured_text for word in ["مرحبا", "أهلا", "عليكم", "السلام", "نبراس"]):
                    hello_gesture()
                    response = "أهلا بك! أنا نيبراس، كيف اقدر اساعدك اليوم؟"
                else:
                    # 3. محادثة عبر Gemini 1.5 Flash
                    try:
                        prompt_instructions = f"""
                                    أنت الروبوت 'نبراس'، مساعد شخصي ذكي. التزم بالقواعد التالية بدقة:
                                    - إذا طلب المستخدم منك (الغناء) أو أي شيء يدل عليه، ابدأ ردك بكلمة [SONG] ثم جملة موافقة قصيرة.
                                    - إذا طلب المستخدم منك (الرقص) أو أي شيء يدل عليه كالهز، ابدأ ردك بكلمة [DANCE] ثم جملة ترحيبية قصيرة.
                                    - إذا سألك عن اسمك، أجب أنك نبراس.
                                    - إذا سألك عن وظيفتك أو هدفك، أجب أنك مساعد شخصي ذكي.
                                    - إذا سألك عن مطورك او صانعك، قل بفخر: 'مطوريني هم طالبات أول وأفضل دفعة ذكاء اصطناعي: العنود، شهد، ندى، ويارا'.
                                    - اجعل ردودك باللهجة السعودية البيضاء، قصيرة جداً ومباشرة.

                                    نص المستخدم: {captured_text}
                                    """
                        res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt_instructions)
                        response = res.text
                        talking_movement()

                        # التحقق مما إذا كان الرد يحتوي على وسم رقص أو غناء
                        if "[DANCE]" in response or "[SONG]" in response:
                            # تنظيف النص من أي وسوم ليتم نطقه بشكل طبيعي
                            response = response.replace("[DANCE]", "").replace("[SONG]", "").strip()

                            # 1. نطق جملة الترحيب (مثلاً: ابشر، من عيوني)
                            text_to_speech_google(response)

                            # 2. تشغيل العرض المدمج (رقص وغناء في نفس الوقت)
                            dance_and_sing_gesture()

                            continue  # العودة لبداية الحلقة للاستماع من جديد

                    except Exception as e:
                        print(f"Gemini Error: {e}")
                        confused_movement()
                        response = "أواجه صعوبة في التفكير الآن."

                text_to_speech_google(response)