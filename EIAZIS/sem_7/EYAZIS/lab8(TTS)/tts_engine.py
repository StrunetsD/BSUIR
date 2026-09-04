import os
import uuid
import win32com.client
import pythoncom


class Voice:
    def __init__(self, voice_object, index):
        self.id = index
        self.name = voice_object.GetDescription()
        try:
            lang_code = voice_object.Id.split('Lang=')[1]
            self.lang = lang_code
        except IndexError:
            self.lang = "N/A"


def get_available_voices():
    """
    Получает список доступных голосов, инициализируя COM для текущего потока.
    """
    pythoncom.CoInitialize()
    speaker = None
    voices_list = []
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        system_voices = speaker.GetVoices()
        for i in range(system_voices.Count):
            voice_obj = system_voices.Item(i)
            voices_list.append(Voice(voice_obj, i))
    except Exception as e:
        print(f"Не удалось получить голоса: {e}")
    return voices_list


def synthesize_speech(text, voice_id, rate, volume, output_dir):
    """
    Синтезирует речь, инициализируя COM для текущего потока.
    """
    pythoncom.CoInitialize()
    speaker = None
    filename = None
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")

        filename_gen = f"{uuid.uuid4()}.wav"
        filepath = os.path.join(output_dir, filename_gen)

        filestream = win32com.client.Dispatch("SAPI.SpFileStream")
        filestream.Open(filepath, 3, True)
        speaker.AudioOutputStream = filestream

        speaker.Voice = speaker.GetVoices().Item(int(voice_id))
        speaker.Volume = int(volume * 100)

        sapi_rate = int((rate - 150) / 20)
        if sapi_rate < -10: sapi_rate = -10
        if sapi_rate > 10: sapi_rate = 10
        speaker.Rate = sapi_rate

        speaker.Speak(text)
        filestream.Close()
        filename = filename_gen

    except Exception as e:
        print(f"Ошибка синтеза речи через win32com: {e}")
        filename = None

    return filename