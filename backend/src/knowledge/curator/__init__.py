"""Init and utils."""
from zope.i18nmessageid import MessageFactory

_ = MessageFactory('knowledge.curator')

def initialize(context):
    """Initializer called when used as a Zope 2 product."""
