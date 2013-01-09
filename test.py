"""
Currently tests:
    * Card functions of equality and compatibility
    * Whether or not a given group of features is a set 
    * Deck solving

TODO: Add file read in tests
"""

from math import factorial
import unittest

from setsolver import is_set, is_feature_a_set, Card, CardDeck, SAME, DIFFERENT

class TestCardFunctions(unittest.TestCase):
    """
    This tests the basic card functions of equality and compatibility.
    """

    def setUp(self):
        """
        Sets up cards for the tests.
        """

        self.cardA = Card({"Color": "purple", "Number": "2", "Shape": "square", "Fill": "empty"})
        self.cardA2 = Card({"Color": "purple", "Number": "2", "Shape": "square", "Fill": "empty"})
        self.cardB = Card({"Color": "blue", "Number": "1", "Shape": "circle", "Fill": "lines"})
        self.cardC = Card({"Color": "black", "Direction": "west", "Polarity": "negative", "Temperature": "cold"})
        self.cardD = Card({"Color": "teal", "Direction": "south", "Polarity": "positive"})
        self.cardE = Card({"Color": "teal", "Direction": "south", "Polarity": "positive", "Temperature": "hot"})

    def test_equal(self):
        """
        Test the equality function that tells whether two cards have equal
        features and  values.
        """

        # these two cards are the same
        self.assertEqual(self.cardA, self.cardA2)
        # these are not
        self.assertNotEqual(self.cardA, self.cardB)
        # want to make sure one card isn't equal to another with a superset of features
        self.assertNotEqual(self.cardD, self.cardE)

    def test_compatible(self):
        """
        Tests the compatibility function that tells whether two cards have
        compatible features.
        """

        # a card should be compatible with itself
        self.assertTrue(self.cardA.compatible(self.cardA))
        # and another card with all the same features
        self.assertTrue(self.cardA.compatible(self.cardB))
        # make sure cards with different features are not compatible
        self.assertFalse(self.cardA.compatible(self.cardC))
        # make sure a card with a superset of features is not compatible with the subset
        self.assertFalse(self.cardC.compatible(self.cardD))

        # test against feature lists
        self.assertTrue(self.cardA.compatible(["Color", "Number", "Shape", "Fill"]))
        self.assertFalse(self.cardA.compatible(["Color", "Number", "Shape"]))
        self.assertFalse(self.cardA.compatible(["Color", "Direction", "Polarity", "Temperature"]))

class TestIsFeatureASet(unittest.TestCase):

    def setUp(self):
        """
        Set up feature value groups, represented as lists, to test for set-ness.
        """

        self.setA = ["blue", "blue", "blue"]
        self.setB = ["blue", "green", "blue"]
        self.setC = ["blue", "red", "green"]
        self.setD = ["blue", "red", "green", "green"]

    def test_same(self):
        """
        Tests whether a feature value group is a set by being same.
        """

        self.assertEqual(is_feature_a_set(*self.setA), SAME)

    def test_different(self):
        """
        Tests whether a feature value group is a set by all values being different.
        """

        self.assertEqual(is_feature_a_set(*self.setC), DIFFERENT)

    def test_false(self):
        """
        Tests feature value groups that aren't sets.
        """

        self.assertFalse(is_feature_a_set(*self.setB))
        self.assertFalse(is_feature_a_set(*self.setD))

class TestDeckSolve(unittest.TestCase):
    """
    Tests different card sets of differing sizes.
    """

    def check_deckfile(self, testfile, setsize):
        """
        This function lets us automatically run tests on a test file
        by using the first comment line as a descriptor of which positions
        are sets.

        It also checks to make sure that all generated combos are in numerical
        order by position, which is important for testing against expected sets,
        and that we are generating the right number of combinations for the
        expected
        """

        deck = CardDeck(load_file = testfile)

        # tally up the number we are generating while we check that they
        # are ordered, otherwise later tests won't work
        generated_combos = 0
        for combo in deck.card_position_combos(setsize):
            generated_combos += 1

            self.assertTrue(all(combo[i] <= combo[i+1]
                    for i in xrange(len(combo)-1)))

        # also want to make sure we are generating the correct number
        # of combinations for this deck and set size
        # note: this is not very efficient
        expected_combos = factorial(len(deck.cards)) / (
            factorial(setsize) * factorial(len(deck.cards) - setsize))

        self.assertEqual(expected_combos, generated_combos)

        # if there's no comments, we can't compare what we expect to what
        # we get using the metadata
        if len(deck.comments) == 0:
            return False

        # note: the set positions need to be in numeric order, ex. 0-3-5
        expected_sets = set([s for s in deck.comments[0].strip(" #").split("|")])

        # for each set in the solved deck, see if the same "fingerprint"
        # exists in the expected sets
        for s in deck.solve(setsize = setsize):
            self.assertIn(s.positions_string(), expected_sets)

    def test_two_features(self):
        """
        Tests only two features.  All two feature pairs are sets.
        """

        self.check_deckfile("tests/twofeatures.set", 2)

    def test_three_features(self):
        """
        Tests three features for the deck.
        """

        self.check_deckfile("tests/threefeatures.set", 3)
        # this actually has no matches inside of it
        self.check_deckfile("tests/threefeaturesusingfour.set", 4)

    def test_four_features(self):
        """
        Tests four features for the deck. Additionally, tests
        using fewer cards than the number of features.
        """

        self.check_deckfile("tests/fourfeatures.set", 4)
        self.check_deckfile("tests/fourfeaturesusingthree.set", 3)


if __name__ == '__main__':

    unittest.main()
