"""Base voter class that all site-specific voters inherit from."""

import logging
from abc import ABC, abstractmethod


class BaseVoter(ABC):
    """Abstract base class for all site-specific voters.

    Subclasses must implement the :meth:`vote` coroutine to perform
    the actual voting logic for a given site.
    """

    def __init__(self, pseudo: str, url: str) -> None:
        """Initialise the voter with the player pseudo and the target URL.

        Args:
            pseudo: The Minecraft username to vote with.
            url: The voting page URL for the site.
        """
        self.pseudo = pseudo
        self.url = url
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def vote(self, page) -> bool:
        """Perform the vote on the site using the provided Playwright page.

        Args:
            page: A Playwright :class:`Page` instance already opened by the
                caller.  The implementation is responsible for navigating,
                filling forms, and confirming the vote.

        Returns:
            ``True`` if the vote was cast successfully, ``False`` otherwise.
        """
