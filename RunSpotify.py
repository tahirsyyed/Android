# You can run multiple tests by just running this test script.
# Import the Spotify_Test from the TestSuit1
import TestSuite1.Spotify_Test
# Run the Spotify_Test
TestSuite1.Spotify_Test.run_me()

#NOTE: This is just for showing how to run multiple tests from different Test folder
# Pandora_test.py may have some error when you run since I just copied and create it for example
# Import the Pandora_test from TestSuit2
import TestSuite2.Pandora_test
# Run the Spotify_test
TestSuite2.Pandora_test.run_me()