import unittest

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.discover("GarnishEdge_App/tests")

    runner = unittest.TextTestRunner()
    runner.run(suite)
