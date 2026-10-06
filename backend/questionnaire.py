"""
questionnaire.py - the single source of truth for the privacy questionnaire.

Every question carries everything the engines need:
  * the answer scale (and therefore the risk value of each answer, 0.0 - 1.0)
  * a weight (how much the question matters inside its category)
  * a severity (drives the priority of the recommendation)
  * the finding text, a short "fix" label and the recommendation text

PRIVACY NOTE: questions only ask "is X visible / enabled?". They never ask the
user to TYPE a phone number, e-mail, address, birth date or password.

EDUCATIONAL NOTE: risk values, weights and severities are educational
assumptions, not measured statistics.
"""
from dataclasses import dataclass
from typing import Optional

# --------------------------------------------------------------------------- #
# Categories (A-J).  "key" is used in code, "label" on screen.
# --------------------------------------------------------------------------- #
CATEGORIES = [
    # key,               letter, questionnaire title,                    score label,          contribution type
    ("profile",           "A", "Profile Visibility",                    "Profile Exposure",   "Exposure contribution"),
    ("personal_info",     "B", "Personal Information",                  "Personal Information", "High exposure contribution"),
    ("location",          "C", "Location Privacy",                      "Location Exposure",  "High exposure contribution"),
    ("content",           "D", "Posts & Content",                       "Content Exposure",   "Content/privacy contribution"),
    ("connections",       "E", "Friends / Followers",                   "Connection Risk",    "Social-engineering risk contribution"),
    ("tagging",           "F", "Tagging & Mentions",                    "Tagging Risk",       "Content/privacy contribution"),
    ("account_security",  "G", "Authentication & Account Security",     "Account Security",   "Account-security risk contribution"),
    ("third_party_apps",  "H", "Third-Party Apps",                      "Third-Party App Risk", "Application-access risk contribution"),
    ("social_engineering", "I", "Messaging & Social Engineering",       "Social Engineering", "Social-engineering risk contribution"),
    ("digital_footprint", "J", "Digital Footprint",                     "Digital Footprint",  "Footprint contribution"),
]
CATEGORY_KEYS = [c[0] for c in CATEGORIES]
CATEGORY_INFO = {
    c[0]: {"key": c[0], "letter": c[1], "title": c[2], "label": c[3], "contribution": c[4]} for c in CATEGORIES
}

# --------------------------------------------------------------------------- #
# Answer scales.  value -> risk (0.0 = lowest assessed risk, 1.0 = highest).
# NOT_SURE is treated as "possibly exposed" (0.6): if you cannot tell, you cannot
# rule the exposure out.
# --------------------------------------------------------------------------- #
SCALES = {
    "public_yn": {"YES": 1.0, "NOT_SURE": 0.6, "NO": 0.0},          # "Is this publicly visible?"
    "visibility": {"PUBLIC": 1.0, "NOT_SURE": 0.6, "FRIENDS": 0.4, "PRIVATE": 0.0},
    "audience": {"EVERYONE": 1.0, "NOT_SURE": 0.6, "FRIENDS": 0.4, "NO_ONE": 0.0},
    "yes_bad": {"YES": 1.0, "SOMETIMES": 0.6, "NOT_SURE": 0.6, "NO": 0.0},    # YES is the risky answer
    "yes_good": {"NO": 1.0, "NOT_SURE": 0.6, "SOMETIMES": 0.4, "YES": 0.0},   # YES is the safe answer (SOMETIMES = partial)
}

FINDING_THRESHOLD = 0.5   # a question produces a finding when its risk is >= this value
SEVERITY_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
PRIORITY_BY_SEVERITY = {"HIGH": "IMMEDIATE", "MEDIUM": "IMPORTANT", "LOW": "GOOD PRACTICE"}
PRIORITY_ORDER = ["IMMEDIATE", "IMPORTANT", "GOOD PRACTICE"]


@dataclass(frozen=True)
class Question:
    id: str
    category: str
    text: str
    scale: str
    weight: int                 # 1 (minor) .. 3 (major) inside the category
    severity: str               # HIGH / MEDIUM / LOW
    finding: str                # shown when the answer is risky
    fix: str                    # short imperative label used by the simulator
    recommendation: str
    control: Optional[str] = None   # label if this question represents a security control

    @property
    def options(self):
        return list(SCALES[self.scale].keys())

    @property
    def safe_answer(self):
        scale = SCALES[self.scale]
        return min(scale, key=scale.get)

    @property
    def finding_type(self):
        return self.id.upper()

    @property
    def priority(self):
        return PRIORITY_BY_SEVERITY[self.severity]

    def risk_of(self, answer):
        return SCALES[self.scale][answer]


def _q(id, cat, text, scale, w, sev, finding, fix, rec, control=None):
    return Question(id, cat, text, scale, w, sev, finding, fix, rec, control)


QUESTIONS = [
    # ---------------- A. Profile Visibility ---------------- #
    _q("profile_visibility", "profile", "Who can see your profile and main posts?", "visibility", 3, "MEDIUM",
       "Profile is visible to the public, which increases how much information can be viewed by anyone.",
       "Set profile to friends-only", "Switch the profile to friends-only/private unless a public presence is intentional (for example a creator or business page)."),
    _q("search_engine_visible", "profile", "Can search engines show your profile in their results?", "yes_bad", 2, "MEDIUM",
       "Profile may appear in search-engine results, making it easy to find by name.",
       "Hide profile from search engines", "Turn off search-engine indexing of your profile in the privacy settings, where the platform offers it."),
    _q("friends_list_public", "profile", "Is your friends/followers list visible to everyone?", "public_yn", 2, "MEDIUM",
       "Friends/followers list is publicly visible, revealing relationships others can use to build trust.",
       "Hide friends list", "Limit who can see your friends/followers list to you or to friends only."),
    _q("discoverable_by_contact", "profile", "Can strangers find your account using your phone number or e-mail address?", "yes_bad", 2, "MEDIUM",
       "Account can be discovered through contact details, linking your identity across services.",
       "Disable lookup by phone/e-mail", "Disable 'find me by phone number / e-mail' in discoverability settings."),

    # ---------------- B. Personal Information ---------------- #
    _q("phone_public", "personal_info", "Is your phone number publicly visible?", "public_yn", 3, "HIGH",
       "Phone number is reported as publicly visible.",
       "Make phone number private", "Limit phone-number visibility to 'Only me' where possible, or remove it from the profile."),
    _q("email_public", "personal_info", "Is your personal e-mail address publicly visible?", "public_yn", 2, "MEDIUM",
       "Personal e-mail address is reported as publicly visible.",
       "Make e-mail private", "Hide your personal e-mail address or use a separate alias for public profiles."),
    _q("birthday_public", "personal_info", "Is your full birth date (including the year) publicly visible?", "public_yn", 3, "MEDIUM",
       "Full birth date is reported as publicly visible (a common identity-verification detail).",
       "Hide full birth date", "Show only day and month (or nothing) and keep the birth year private."),
    _q("home_info_public", "personal_info", "Is home-related information (address, street, neighbourhood or home photos) publicly visible?", "public_yn", 3, "HIGH",
       "Home-related information is reported as publicly visible.",
       "Remove home details", "Remove street/neighbourhood details and avoid photos that show your house number or surroundings."),
    _q("workplace_public", "personal_info", "Is your workplace publicly visible?", "public_yn", 2, "MEDIUM",
       "Workplace is reported as publicly visible.",
       "Make workplace private", "Show your employer only to connections, or leave it off personal profiles."),
    _q("education_public", "personal_info", "Is your school/college publicly visible?", "public_yn", 1, "LOW",
       "School/college information is reported as publicly visible.",
       "Make education private", "Limit education details to friends or remove details that are not needed."),
    _q("relationship_public", "personal_info", "Are your relationship or family details (partner, relatives) publicly visible?", "public_yn", 2, "MEDIUM",
       "Relationship/family details are reported as publicly visible.",
       "Hide family details", "Hide family and relationship links, or limit them to close friends."),

    # ---------------- C. Location Privacy ---------------- #
    _q("location_public", "location", "Do you publicly share your current city or location on your profile or posts?", "yes_bad", 3, "HIGH",
       "Location is publicly shared.",
       "Remove public location", "Remove public location details from your profile and posts unless you intentionally need them."),
    _q("realtime_location", "location", "Do you share your real-time location (live location, 'now at...' posts)?", "yes_bad", 3, "HIGH",
       "Real-time location sharing is enabled.",
       "Stop real-time location sharing", "Avoid publicly broadcasting real-time location. Posting a photo after you have left the place reduces immediate exposure."),
    _q("location_tagging", "location", "Do you add geotags/location tags to your posts?", "yes_bad", 2, "MEDIUM",
       "Posts are geotagged, which can reveal places you visit.",
       "Turn off geotagging", "Turn off automatic geotagging and add a location only when it is really needed."),
    _q("public_checkins", "location", "Do you make public check-ins at places?", "yes_bad", 2, "MEDIUM",
       "Public check-ins reveal where you are or usually go.",
       "Stop public check-ins", "Limit check-ins to close friends, or stop using them."),
    _q("travel_posts", "location", "Do you post travel plans before or during a trip?", "yes_bad", 2, "HIGH",
       "Travel plans are posted before or during trips, signalling when you are away.",
       "Stop posting travel plans", "Share trip photos after you return instead of announcing dates and destinations in advance."),
    _q("work_school_location", "location", "Do your posts show your workplace or school location (badges, buildings, daily commute)?", "yes_bad", 2, "MEDIUM",
       "Posts reveal work/school locations or commute patterns.",
       "Stop posting work/school location", "Avoid posting identifiable work/school locations and daily routines."),
    _q("frequent_places", "location", "Do your public posts reveal places you visit regularly (same gym, cafe, route)?", "yes_bad", 1, "LOW",
       "Posts reveal regular places, which can expose routines.",
       "Vary or delay routine-place posts", "Post about regular places with a delay, or less often, to avoid exposing routines."),

    # ---------------- D. Posts & Content ---------------- #
    _q("posts_public", "content", "Who can see your posts?", "visibility", 3, "MEDIUM",
       "Posts are publicly visible.",
       "Limit post audience", "Set the default audience of new posts to friends, and review the audience of older posts."),
    _q("photo_metadata_unaware", "content", "Do you upload original photos without checking or removing embedded metadata (EXIF)?", "yes_bad", 2, "MEDIUM",
       "Photos may be shared with embedded metadata (EXIF) such as device or location details.",
       "Strip photo metadata", "Remove metadata from photos before sharing (see tools/metadata_viewer.py) or rely on platforms that strip it."),
    _q("sensitive_in_photos", "content", "Have you posted photos showing badges, documents, vehicle plates, tickets or computer screens?", "yes_bad", 2, "HIGH",
       "Photos may reveal badges, documents, plates, tickets or screens.",
       "Check photos for sensitive details", "Check photo backgrounds before posting and delete or crop images that show documents, badges, plates or screens."),
    _q("children_photos_public", "content", "Do you publicly post identifiable photos of children (your own or others')?", "yes_bad", 2, "HIGH",
       "Identifiable photos of children are shared publicly.",
       "Restrict photos of children", "Share photos of children only with trusted people, and avoid showing school names or uniforms."),

    # ---------------- E. Friends / Followers ---------------- #
    _q("unknown_connections", "connections", "Do you accept connection/friend requests from people you do not know?", "yes_bad", 3, "HIGH",
       "Connection requests from unknown people are accepted.",
       "Stop accepting unknown requests", "Verify unfamiliar profiles before accepting connections."),
    _q("follower_approval", "connections", "Do you approve new followers/friends manually before they can see your content?", "yes_good", 2, "MEDIUM",
       "New followers/friends are not manually approved.",
       "Require follower approval", "Enable manual approval of followers/friend requests."),
    _q("connections_audited", "connections", "Have you reviewed and removed old or unfamiliar connections in the last 12 months?", "yes_good", 2, "LOW",
       "Connections have not been reviewed recently.",
       "Review connections list", "Review your connections twice a year and remove people you no longer know or trust."),
    _q("open_messages", "connections", "Can people you do not know send you direct messages?", "yes_bad", 2, "MEDIUM",
       "Strangers can send direct messages.",
       "Restrict who can message you", "Route messages from non-connections into a 'requests' folder or disable them."),

    # ---------------- F. Tagging & Mentions ---------------- #
    _q("who_can_tag", "tagging", "Who is allowed to tag you in posts and photos?", "audience", 2, "MEDIUM",
       "Anyone is allowed to tag the account.",
       "Limit who can tag you", "Limit tagging to friends or turn tagging off."),
    _q("tag_review_enabled", "tagging", "Do you review tags before they appear on your profile (tag review turned on)?", "yes_good", 3, "MEDIUM",
       "Tag review is disabled, so tags from others appear without approval.",
       "Enable tag review", "Enable tag review so you approve tags before they appear.",
       control="Tag review"),
    _q("tagged_auto_appear", "tagging", "Do posts you are tagged in appear on your profile automatically?", "yes_bad", 2, "MEDIUM",
       "Tagged posts appear on the profile automatically.",
       "Stop auto-showing tagged posts", "Require approval before tagged posts appear on your profile."),
    _q("others_tag_locations", "tagging", "Do other people often tag you at places or events?", "yes_bad", 2, "MEDIUM",
       "Other people's posts can reveal where you are, even if you post little yourself.",
       "Ask friends not to tag your location", "Ask friends not to tag your location and enable review of location tags."),
    _q("unknown_mentions", "tagging", "Can people you do not know mention you?", "yes_bad", 1, "LOW",
       "Unknown people can mention the account.",
       "Limit mentions", "Restrict mentions to friends/followers to reduce harassment and spam."),

    # ---------------- G. Authentication & Account Security ---------------- #
    _q("mfa_enabled", "account_security", "Do you use multi-factor authentication (MFA)?", "yes_good", 3, "HIGH",
       "Multi-factor authentication (MFA) is disabled.",
       "Enable MFA", "Enable multi-factor authentication using the strongest supported method (security key or authenticator app).",
       control="Multi-factor authentication"),
    _q("password_reuse_reported", "account_security", "Do you reuse the same password on more than one account?", "yes_bad", 3, "HIGH",
       "Password reuse is reported, so one breach could expose several accounts.",
       "Use unique passwords", "Use a unique, long password for every account (a password manager makes this practical).",
       control="Unique passwords"),
    _q("password_manager", "account_security", "Do you use a password manager?", "yes_good", 1, "LOW",
       "No password manager in use.",
       "Start using a password manager", "Use a reputable password manager to create and store unique passwords.",
       control="Password manager"),
    _q("login_alerts_enabled", "account_security", "Are login alerts (new-device notifications) enabled?", "yes_good", 2, "MEDIUM",
       "Login alerts are disabled.",
       "Enable login alerts", "Enable login alerts so unusual sign-ins are noticed quickly.",
       control="Login alerts"),
    _q("recovery_reviewed", "account_security", "Have you reviewed your account-recovery options (recovery e-mail/phone) recently?", "yes_good", 2, "MEDIUM",
       "Recovery information has not been reviewed.",
       "Review recovery options", "Check that recovery e-mail/phone are current and under your control.",
       control="Recovery options reviewed"),
    _q("sessions_reviewed", "account_security", "Do you review active sessions/logged-in devices?", "yes_good", 2, "MEDIUM",
       "Active sessions are not reviewed.",
       "Review active sessions", "Review active sessions and log out of devices you do not recognise or no longer use.",
       control="Active sessions reviewed"),
    _q("unknown_devices_checked", "account_security", "Do you check the list of known/trusted devices for unknown entries?", "yes_good", 1, "LOW",
       "Trusted-device list is not checked.",
       "Check trusted devices", "Remove unknown or old devices from your trusted-device list.",
       control="Trusted devices checked"),

    # ---------------- H. Third-Party Apps ---------------- #
    _q("third_party_apps_reviewed", "third_party_apps", "Do you regularly review the third-party apps connected to your account?", "yes_good", 3, "MEDIUM",
       "Third-party apps have never or rarely been reviewed.",
       "Review connected apps", "Regularly review and revoke unnecessary application access (principle of least privilege).",
       control="Connected apps reviewed"),
    _q("unused_apps_connected", "third_party_apps", "Do you have connected apps you no longer use?", "yes_bad", 2, "MEDIUM",
       "Unused apps still have access to the account.",
       "Remove unused apps", "Remove unused integrations from your account settings."),
    _q("broad_permissions", "third_party_apps", "Have you granted apps broad permissions (read messages, post for you, access contacts)?", "yes_bad", 2, "HIGH",
       "Apps may hold broad permissions beyond what they need.",
       "Reduce app permissions", "Limit permissions to the minimum an app really needs."),
    _q("social_login_overuse", "third_party_apps", "Do you use 'Sign in with social account' on many websites and apps?", "yes_bad", 1, "LOW",
       "Many sites are linked through social sign-in.",
       "Reduce social sign-ins", "Use social sign-in sparingly; remove links to sites you no longer use."),
    _q("old_integrations", "third_party_apps", "Are there integrations older than a year that you have not looked at since?", "yes_bad", 1, "LOW",
       "Old integrations remain connected without review.",
       "Review old integrations", "Review integrations older than a year and remove what is not needed."),

    # ---------------- I. Messaging & Social Engineering ---------------- #
    _q("responds_to_unknown_dms", "social_engineering", "Do you reply to unexpected messages from unknown accounts?", "yes_bad", 2, "MEDIUM",
       "Unexpected messages from unknown accounts get replies.",
       "Stop replying to unknown DMs", "Do not engage with unexpected messages; report and block suspicious accounts."),
    _q("suspicious_link_awareness", "social_engineering", "Can you recognise suspicious links and messages (urgency, odd addresses, too-good-to-be-true offers)?", "yes_good", 2, "MEDIUM",
       "Awareness of suspicious links/messages is low.",
       "Learn to spot suspicious links", "Learn the common signs of phishing and verify links before clicking."),
    _q("clicks_unexpected_links", "social_engineering", "Do you click unexpected links, even from friends, without checking them first?", "yes_bad", 3, "HIGH",
       "Unexpected links are clicked without verification.",
       "Verify links before clicking", "Verify unexpected links with the sender through another channel before opening them."),
    _q("shared_verification_code", "social_engineering", "Have you ever shared a verification/one-time code with someone who asked for it?", "yes_bad", 3, "HIGH",
       "Verification codes have been shared with another person.",
       "Never share verification codes", "Never share verification codes. No genuine service will ask you to read one out."),
    _q("shares_info_in_dms", "social_engineering", "Do you share personal information in messages with people you have not verified?", "yes_bad", 2, "MEDIUM",
       "Personal information is shared in messages with unverified people.",
       "Stop sharing personal info in DMs", "Share personal information only after confirming who you are talking to."),
    _q("verifies_urgent_requests", "social_engineering", "If a friend messages you urgently for money or help, do you verify through another channel (call, in person)?", "yes_good", 2, "MEDIUM",
       "Urgent requests from 'friends' are not verified through another channel.",
       "Verify urgent requests", "Confirm urgent requests by calling the person on a known number - impersonated accounts are common."),
    _q("giveaway_participation", "social_engineering", "Do you take part in giveaways or 'you have won' offers that ask for details or logins?", "yes_bad", 2, "MEDIUM",
       "Participation in suspicious giveaways is reported.",
       "Avoid giveaways asking for details", "Avoid prize offers that ask for personal details, logins or fees."),

    # ---------------- J. Digital Footprint ---------------- #
    _q("old_posts_reviewed", "digital_footprint", "Do you regularly review your old public posts?", "yes_good", 2, "MEDIUM",
       "Old public posts have not been reviewed.",
       "Review old posts", "Review old public posts and remove or restrict those you would not share today."),
    _q("old_accounts_unused", "digital_footprint", "Do you have old or unused social-media accounts that are still active?", "yes_bad", 2, "MEDIUM",
       "Old/unused accounts are still active.",
       "Close unused accounts", "Delete or secure old accounts you no longer use."),
    _q("public_comments", "digital_footprint", "Do you often leave public comments that include personal details or opinions you would not want an employer or school to see?", "yes_bad", 1, "LOW",
       "Public comments may add to an unwanted digital footprint.",
       "Review public comments", "Think before commenting publicly; review and delete old comments you would not repeat today."),
    _q("profile_history_public", "digital_footprint", "Are your old profile details (past photos, bios, usernames) still publicly visible?", "yes_bad", 1, "LOW",
       "Past profile content is still visible.",
       "Clean profile history", "Remove old profile photos and bios that expose details you no longer share."),
    _q("privacy_settings_reviewed", "digital_footprint", "Have you reviewed your privacy settings in the last 6 months?", "yes_good", 2, "MEDIUM",
       "Privacy settings have not been reviewed recently.",
       "Review privacy settings", "Review privacy settings at least twice a year - platforms change defaults.",
       control="Privacy settings reviewed"),
    _q("self_search_done", "digital_footprint", "Have you searched your own name online to see what is publicly visible?", "yes_good", 1, "LOW",
       "No self-check of what is publicly visible about the account.",
       "Search your own name", "Search your own name from a signed-out browser to see what others can see.",
       control="Self-search done"),
]

QUESTION_BY_ID = {q.id: q for q in QUESTIONS}
assert len(QUESTION_BY_ID) == len(QUESTIONS), "duplicate question ids"
# Questions that represent a security/privacy control the user can switch on.
CONTROL_QUESTIONS = [q for q in QUESTIONS if q.control]

# --------------------------------------------------------------------------- #
# Category-level awareness guidance (shown when a category scores HIGH or worse)
# --------------------------------------------------------------------------- #
AWARENESS_TIPS = {
    "profile": "Visibility is not automatically unsafe, but every extra public item increases what a stranger can learn. Decide deliberately what must be public.",
    "personal_info": "Contact details, birth date and workplace are the raw material for impersonation and identity-related scams. Share the minimum.",
    "location": "Real-time and habitual location posts show when you are away and where you will be. Delay or generalise location content.",
    "content": "Photos and posts can reveal more than intended (backgrounds, badges, metadata). Check before you post.",
    "connections": "Unknown connections are a common first step in social-engineering attempts. Verify before accepting.",
    "tagging": "Other people's posts can expose you even when you post very little. Tag review gives you a veto.",
    "account_security": "Privacy and security overlap but differ: strong settings do not help if the account is taken over. Turn on MFA and use unique passwords.",
    "third_party_apps": "Every connected app is another door into your account. Apply least privilege and revoke what you do not use.",
    "social_engineering": "Scammers exploit urgency and trust. Never share verification codes; verify requests through a second channel.",
    "digital_footprint": "Old posts and old accounts keep working against you long after you forget them. Schedule a periodic review.",
}

# --------------------------------------------------------------------------- #
# Printable privacy checklist (spec section 38)
# --------------------------------------------------------------------------- #
CHECKLIST = [
    "Review profile visibility",
    "Hide unnecessary contact information",
    "Review birth-date visibility",
    "Review location sharing",
    "Avoid unnecessary real-time location posts",
    "Review tagging permissions",
    "Review followers/friends",
    "Verify unfamiliar requests",
    "Enable MFA",
    "Enable login alerts where available",
    "Review active sessions",
    "Review connected apps",
    "Remove unused integrations",
    "Review old public posts",
    "Review photo privacy",
    "Be cautious with unexpected links",
    "Never share verification codes",
    "Review privacy settings periodically",
]

# --------------------------------------------------------------------------- #
# Fictional demonstration profile (spec section 32). Entirely synthetic.
# The listed answers follow the brief; every question not listed is answered with its
# riskiest value except the "SAFE_IN_DEMO" ones, so the demo shows a clearly exposed profile.
# --------------------------------------------------------------------------- #
DEMO_OVERRIDES = {
    "profile_visibility": "PUBLIC", "phone_public": "YES", "email_public": "NO", "birthday_public": "YES",
    "location_public": "YES", "realtime_location": "YES", "public_checkins": "YES", "travel_posts": "YES",
    "unknown_connections": "YES", "tag_review_enabled": "NO", "mfa_enabled": "NO",
    "login_alerts_enabled": "NO", "third_party_apps_reviewed": "NO", "old_posts_reviewed": "NO",
}
SAFE_IN_DEMO = {  # a few things the fictional person does reasonably well
    "children_photos_public": "NO", "shared_verification_code": "NO", "giveaway_participation": "NO",
    "clicks_unexpected_links": "NO", "shares_info_in_dms": "NO", "responds_to_unknown_dms": "NO",
    "sensitive_in_photos": "NO", "home_info_public": "NO", "relationship_public": "NO",
    "education_public": "NO", "workplace_public": "NO", "broad_permissions": "NO",
    "social_login_overuse": "NO", "old_integrations": "NO", "unknown_mentions": "NO",
    "public_comments": "NO", "profile_history_public": "NO",
}
# Settings changed in the demo "improvement" simulation (spec section 32).
DEMO_FIX_IDS = ["phone_public", "birthday_public", "location_public", "travel_posts", "unknown_connections",
                "tag_review_enabled", "mfa_enabled", "login_alerts_enabled", "third_party_apps_reviewed"]


def worst_answers():
    """Highest-risk answer for every question."""
    return {q.id: max(SCALES[q.scale], key=SCALES[q.scale].get) for q in QUESTIONS}


def safest_answers():
    """Lowest-risk answer for every question."""
    return {q.id: q.safe_answer for q in QUESTIONS}


def demo_profile_answers():
    """The fictional demo profile used for the live demonstration."""
    answers = worst_answers()
    answers.update(SAFE_IN_DEMO)
    answers.update(DEMO_OVERRIDES)
    return answers


def public_questionnaire():
    """JSON-friendly questionnaire for the frontend (no scoring internals)."""
    out = []
    for cat in CATEGORIES:
        out.append({
            "key": cat[0], "letter": cat[1], "title": cat[2],
            "questions": [{"id": q.id, "text": q.text, "options": q.options}
                          for q in QUESTIONS if q.category == cat[0]],
        })
    return out
