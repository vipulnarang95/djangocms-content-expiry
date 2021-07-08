from cms.test_utils.testcases import CMSTestCase


class BasicTest(CMSTestCase):
    """
    Basic test to ensure test suit runs
    """
    def test_fail(self):
        self.assertTrue(False)
