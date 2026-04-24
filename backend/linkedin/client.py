import urllib.parse

import httpx

PROFILE_URL = "https://api.linkedin.com/v2/userinfo"
POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"
PERSON_URL = "https://api.linkedin.com/v2/me"
SOCIAL_ACTIONS_URL = "https://api.linkedin.com/v2/socialActions/{post_urn}"


class LinkedInClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def get_profile(self) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(PROFILE_URL, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_post_analytics(self, post_urn: str) -> dict:
        """Fetch likes, comments, and shares for a published post.
        Note: impressions require LinkedIn partner access and are not available here."""
        encoded_urn = urllib.parse.quote(post_urn, safe="")
        url = SOCIAL_ACTIONS_URL.format(post_urn=encoded_urn)
        headers = {**self.headers, "X-Restli-Protocol-Version": "2.0.0"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                return {"likes": 0, "comments": 0, "shares": 0}
            data = response.json()
            return {
                "likes": data.get("likesSummary", {}).get("totalLikes", 0),
                "comments": data.get("commentsSummary", {}).get("totalFirstLevelComments", 0),
                "shares": data.get("sharesSummary", {}).get("totalShares", 0),
            }

    async def publish_post(self, author_urn: str, content: str) -> dict:
        """Publish a text post to LinkedIn."""
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(POSTS_URL, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
