import logging
from optparse import OptionParser
import sys

# Constant string values indicating the type of match
SAME = "Same"  # all features are the same in the card set
DIFFERENT = "Different"  # all features are different in the card set

# format for log messages
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logger = logging.getLogger("setsolver")


def is_set(*cards):
    """
    Tests whether a batch of cards is a valid set or not.

    Returns a dictionary of set match types if so, False otherwise
    """

    # can't have a set without any cards
    if len(cards) == 0:
        return False

    set_types = dict()

    # for each feature, check to see if the card values for specific feature
    # is valid for a set and add whether the set is from being all different
    # or all the same
    for feat in cards[0].get_feature_names():
        set_type = is_feature_a_set(*[card.features[feat] for card in cards])
        if not set_type:
            return False
        set_types[feat] = set_type

    return set_types


def is_feature_a_set(*feat_values):
    """
    Tests a batch of features to see if the conditions for a set are met.

    Returns setsolver.SAME if they are all the same, setsolver.DIFFERENT
    if all different, False otherwise.
    """

    collapse = set(feat_values)

    # all features are the same or all features are different
    # if all the features are the same, the length of the collapsed set will be 1
    # if all of the features are different, the length of the collapse set
    #   will match the number of args
    if len(collapse) == 1:
        return SAME
    elif len(collapse) == len(feat_values):
        return DIFFERENT
    else:
        return False


class Card:
    """
    Card class, containing the features of each card.
    """

    def __init__(self, features):
        """
        Initialize a card, given a dictionary of features and their values.
        """

        self.features = features

    def __str__(self):
        """
        String is all of the value (feature) pairs.
        """

        return ',\t'.join(["%s (%s)" % (value, feat) for feat, value
                           in self.features.items()])

    def __eq__(firstCard, SecondCard):
        """
        Determines if a card is equal to another card by comparing all
        features between them.
        """

        # have to check for compatibility first
        if not firstCard.compatible(SecondCard):
            return False

        for feat in firstCard.features:
            if firstCard.features[feat] != SecondCard.features[feat]:
                return False
        return True

    def compatible(firstCard, secondCardOrFeatures):
        """
        Determines if two cards are compatible--that is, if their feature
        categories are equivalent.  Can also use this with a list.

        returns True if compatible, False otherwise
        """

        # convert this to a list of features, if it's a card
        # this is technically a bad way to do this but it's quick and works
        if isinstance(secondCardOrFeatures, Card):
            secondCardOrFeatures = secondCardOrFeatures.get_feature_names()

        # compatible feature sets won't have any names different between them
        return len(set(firstCard.get_feature_names()).symmetric_difference(
            set(secondCardOrFeatures))) == 0

    def get_feature_names(self):
        """
        Returns the feature names of this card.
        """

        return self.features.keys()


class CardSet:
    """
    Keeps track of a card set, the cards' positions in the deck,
    and the types of sets the features represent.
    """

    def __init__(self, cards, positions=None):
        """
        Takes a list of compatible cards, and optionally their positions
        in a Deck.
        """

        self.card_positions = positions
        self.cards = cards
        self.set_types = None

    def check_set(self):
        """
        Checks whether this set of cards is actually a set.  Useful for more
        one off uses--CardDeck doesn't use this for efficiency.
        """

        return is_set(*self.cards)

    def __str__(self):
        """
        String converstion.  Will default to printing out card positions
        only if they exist, otherwise prints out cards.
        """

        if self.card_positions:
            return self.positions_string()
        else:
            return self.cards_string()

    def positions_string(self):
        """
        Returns a string with all of the card positions from the deck, separated
        by dashes.
        """
        if self.card_positions:
            return u'%s' % "-".join([str(position)
                                     for position in self.card_positions])
        else:
            return "No positions available"

    def cards_string(self):
        """
        Returns a string with all of the cards in this set, separated by /
        """

        return u'%s' % " / ".join([str(card) for card in self.cards])


class CardDeck:
    """
    Class that can load a set of cards and their features from a file.
    """

    def __init__(self, load_file=None):
        """
        Initializes the class and optionally loads a card file.
        """

        self.features = None
        self.cards = None
        self.sets = list()
        self.feature_values = dict()

        if load_file:
            self.load_file(load_file)

    def load_file(self, filename):
        """
        Loads a list of cards from a file.  The file should be tab delineated
        and have one feature in each field.

        Lines can be commented out by starting with #.  The first line should
        be the feature names.
        """

        # should start out with a clean slate for these variables
        self.cards = list()
        self.features = None

        # keep track of comment lines--this way people can add custom metadata
        # such as for testing or print out the comments later
        self.comments = list()

        with open(filename, 'r') as f:

            for line in f:
                line = line.strip()

                # skip over comment lines and empty lines
                if len(line) == 0 or line[0] == "#":
                    self.comments.append(line)
                    continue

                # fields determined by a tab delineated line
                fields = line.split("\t")

                # if we don't have this yet, it's the first non-commented line and
                # we'll use those fields as features
                if not self.features:
                    self.features = fields
                    [self.feature_values.update({feat: set()}) for feat
                        in self.features]
                    continue

                # Don't load a corrupt line that doesn't have fields for all
                # features; warn about it
                if len(fields) != len(self.features):
                    logger.warn("This line is corrupt: %s" % line)
                    continue

                card_features = dict(zip(self.features, fields))

                # Create the card and add it to the list
                # doing this manually instead of the addCard function--we don't
                # need the overhead of checking the features when loading
                # from a file
                c = Card(card_features)
                self.cards.append(c)

                # We want a list of all distinct feature values,
                # so add in any new ones
                [self.feature_values[feat].add(value)
                    for feat, value in card_features.items()
                    if value not in self.feature_values[feat]]

    def add_card(self, card):
        """
        Adds a card to the deck if it has compatible features.

        Return True if the card was successfully added, False otherwise.
        """

        # if there are no existing features, this is the first card we
        # see and we'll make its features those of the set
        if not len(self.features):
            self.features = card.get_feature_names()
        # If the card isn't compatible, return False
        else:
            if not card.compatible(self.features):
                return False

        # add card to the end of the pile
        self.cards.append(card)
        return True

    def print_cards(self):
        """
        Prints out a list of the cards in the deck.
        """

        print("Cards: ")
        for i in range(0, len(self.cards)):
            print("\tCard %s: %s" % (i, self.cards[i]))

    def print_feature_values(self):
        """
        Prints out all of the possible feature values in this deck.
        """

        print("Feature values: ")
        for feat, values in self.feature_values.items():
            print("\t%s: %s" % (feat, ", ".join(values)))

    def generate_card_combos(self, items, nitems):
        """
        Generates unique combinations of cards in groups of n.

        Call it with numbers and it will give combinations of card numbers,
        which is useful to pull them from the deck. Call with cards and it
        will give lists of cards.
        """

        if nitems == 0:
            yield []
        else:
            for i in range(0, len(items)):
                for item in self.generate_card_combos(
                        items[i + 1:], nitems - 1):
                    yield [items[i]] + item

    def card_position_combos(self, setsize):
        """
        A placeholder function to call the card combination generator for orders.
        """

        return self.generate_card_combos(range(len(self.cards)), setsize)

    def card_combinations(self, setsize):
        """
        A placeholder function to call the card combination generator for cards.
        """

        return self.generate_card_combos(self.cards, setsize)

    def solve(self, setsize=3):
        """
        Finds the solutions for this set of cards give a set size.  The
        default set size is 3, like in the game.

        Returns the list of CardSet matches.
        """

        # reset this just in case
        self.sets = list()

        if setsize > len(self.features):
            logger.warning("Solving for a set size of %d, but only have %d features." % (
                setsize, len(self.features)))

        for combo in self.card_position_combos(setsize):
            set_match = is_set(*[self.cards[position] for position in combo])
            if set_match:
                self.sets.append(CardSet([self.cards[position]
                                          for position in combo], combo))
                logger.debug("Set is a match: %s" % "-".join([str(position)
                                                              for position in combo]))
            else:
                logger.debug("Set is not a match: %s" % "-".join([str(position)
                                                                  for position in combo]))

        return self.sets

    def print_sets(self):
        """
        Print all of the sets found.
        """

        if not self.sets:
            print("No matches found.")
            return

        print("Sets:")
        for cardset in self.sets:
            print("\t%s" % cardset)


def run_solver(infile, setsize=3):
    """
    Run the solver on a given file, printing out deck metadata and the results.
    """

    s = CardDeck(infile)
    s.print_feature_values()
    s.print_cards()
    s.solve(setsize=setsize)
    s.print_sets()

##########################################################################
# STANDALONE SCRIPT ENABLING BELOW
##########################################################################


default_parse_options = {
    "setsize": 3,
    "quiet": False,
    "debug": False,
}


def parser_setup():
    """
    Set up the command line argument parser.

    Currently using OptionParser, because it runs in versions of Python under
    2.7.
    """

    parser = OptionParser()

    parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                      help="Don't print info messages to standard out, only warnings and errors.")
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
                      help="Print all debug messages to standard out.")

    parser.add_option("-s", "--setsize", dest="setsize", type="int",
                      help="The size of the set to make.  Default is %default.",
                      metavar="SETSIZE")

    parser.set_defaults(**default_parse_options)
    parser.set_defaults(quiet=False, debug=False)

    return parser


if __name__ == '__main__':

    parser = parser_setup()
    (poptions, pargs) = parser.parse_args()

    if poptions.quiet:
        logging.basicConfig(level=logging.WARNING, format=log_format)
    elif poptions.debug:
        logging.basicConfig(level=logging.DEBUG, format=log_format)
    else:
        # Set up the logging levels
        logging.basicConfig(level=logging.INFO, format=log_format)

    # only positional argument is the input file
    if len(pargs) < 1:
        print("Error: no input file to load!", file=sys.stderr)
        parser.print_help()
        sys.exit(0)
    else:
        infile = pargs[0]

    run_solver(infile, poptions.setsize)
