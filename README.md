## Audio-driven keyframes

A script to help keyframe objects' translation in response to an audio track. Useful for the generation of speakers and audio driven animations.
Only works on 8bit mono and stereo wav files due to limitations in the built in python wave modules. This script is intended for rendering purposes more than realtime as the effect is much better with motion blur turned on.

Demo: https://youtu.be/oTezAIOGCXQ

**User Manual:**

1. Open a .wav file in the open file dialog
2. Choose a channel from which to take audio data. (only applies to stereo tracks)
3. Choose an axis in which to move the object.
4. Choose a level of detail as a percentage. 1 is one key per frame, 100 is the maximum density (one key for every piece of audio data)
5. Set a range between which you would like the object to move. An easy workflow would be to select the object, ensure that you have selected the desired value.
   Move the object to the minimum distance and press the left arrow button (<). Similarly, move the object to the maximum distance and hit the right arrow (>)
6. Autolock is usually left off for testing purposes. If selected it will automatically lock the object from receiving any more keyframes if the script is run a second time.
   Its most useful for distinguishing between multiple objects which have been keyed. Note: deleting keys will automatically unlock any locked object.
7. Ensure the object is selected and press Generate Keyframes to create the keys.
8. Similarly, ensure the object is selected and the desired axis is selected when pressing Delete Keyframes as it will only delete in the axis chosen.
