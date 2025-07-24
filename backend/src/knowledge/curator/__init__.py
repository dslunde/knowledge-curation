"""Init and utils."""

from zope.i18nmessageid import MessageFactory


PACKAGE_NAME = "knowledge.curator"
_ = MessageFactory(PACKAGE_NAME)


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
