# from audioReader import AudioReader
import re
import sys
import os
import logging

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

from PyQt5.QtCore import QThread

class SpeechToText(QThread):
    # Audio recording parameters
    # RATE = 16000
    # CHUNK = int(RATE / 10)  # 100ms

    def __init__(self, audioReader, rate):#,gui):
        super().__init__()
        # self.gui = gui
        self.outputPath = os.path.abspath(__file__ + "/../../../../../") + '/resources/raw_data/'
        self.word_count = 0
        self.audioReader = audioReader
        # See http://g.co/cloud/speech/docs/languages
        # for a list of supported languages.
        language_code = 'en-US'  # a BCP-47 language tag
        self.client = speech.SpeechClient()
        config = types.RecognitionConfig(
                encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=rate,
                language_code=language_code)
        self.streaming_config = types.StreamingRecognitionConfig(
                config=config,
                interim_results=True)

    def get_word_count(self):
        return self.word_count

    def run(self):
        """Iterates through server responses and prints them.

        The responses passed is a generator that will block until a response
        is provided by the server.

        Each response may contain multiple results, and each result may contain
        multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
        print only the transcription for the top alternative of the top result.

        In this case, responses are provided for interim results as well. If the
        response is an interim one, print a line feed at the end of it, to allow
        the next result to overwrite it, until the response is a final one. For the
        final one, print a newline to preserve the finalized transcription.
        """

        # with AudioReader(self.RATE, self.CHUNK) as self.stream:
        audio_generator = self.audioReader.generator()
        requests = (types.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)
        responses = self.client.streaming_recognize(self.streaming_config, requests)

        # Now, put the transcription responses to use.
        with open(self.outputPath + 'output.txt', 'w') as txt:
            for response in responses:
                if not response.results:
                    continue

                # The `results` list is consecutive. For streaming, we only care about
                # the first result being considered, since once it's `is_final`, it
                # moves on to considering the next utterance.
                result = response.results[0]
                if not result.alternatives:
                    continue

                # Display the transcription of the top alternative.
                transcript = result.alternatives[0].transcript

                # Display interim results, but with a carriage return at the end of the
                # line, so subsequent lines will overwrite them.
                #
                # If the previous result was longer than this one, we need to print
                # some extra spaces to overwrite the previous result

                if result.is_final:
                    self.putText(transcript)
                    print(transcript)
                    txt.write(transcript + '.\n')
                    txt.flush()

                    # Exit recognition if any of the transcribed phrases could be
                    # one of our keywords.
                    if self.audioReader.closed:
                        logging.info("SpeechToText closed")
                        break

    def putText(self, text):
        logging.info('detected: ' + text)
        self.word_count += len(text.split())

    # def stopRecording(self):
    #     self.audioReader.closed = True
