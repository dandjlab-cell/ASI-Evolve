"""Premiere prproj ClassIDs.

Verified in Brain/Knowledge/API Integration/Premiere prproj Reverse Engineering Method.md
and Brain/Knowledge/API Integration/Premiere prproj Media Chain and Clip Placement Graph.md.

These are stable across Premiere versions — the schema versions on individual
elements (the `Version="N"` attribute) change, but ClassIDs are global identifiers.
"""

# Project / bin / media chain
CID_BIN_PROJECT_ITEM = "dbfd6653-24da-480e-a35e-ba45e9504e4b"
CID_CLIP_PROJECT_ITEM = "cb4e0ed7-aca1-4171-8525-e3658dec06dd"
CID_MASTER_CLIP = "fb11c33a-b0a9-4465-aa94-b6d5db2628cf"
CID_MEDIA = "7a5c103e-f3ac-4391-b6b4-7cc3d2f9a7ff"
CID_VIDEO_STREAM = "a36e4719-3ec6-4a0c-ab11-8b4aab377aa5"
CID_VIDEO_MEDIA_SOURCE = "e64ddf74-8fac-4682-8aa8-0e0ca2248949"
CID_CLIP_LOGGING_INFO = "77ab7fdd-dcdf-465d-9906-7a330ca1e738"
CID_VIDEO_CLIP = "9308dbef-2440-4acb-9ab2-953b9a4e82ec"

# Sequence / clip placement
CID_VIDEO_CLIP_TRACK_ITEM = "368b0406-29e3-4923-9fcd-094fbf9a1089"
CID_CLIP_CHANNEL_GROUP_VECTOR_SERIALIZER = "a3127a8c-95d4-456e-a7f5-171b3f922426"
CID_MARKERS = "bee50706-b524-416c-9f03-b596ce5f6866"
CID_SUB_CLIP = "e0c58dc9-dbdd-4166-aef7-5db7e3f22e84"
CID_VIDEO_COMPONENT_CHAIN = "0970e08a-f58f-4108-b29a-1a717b8e12e2"

# Audio chain — ClassIDs verified from AUDIO_REF_A.prproj (2026-05-01)
CID_AUDIO_MEDIA_SOURCE = "f588da05-fc2a-4fbc-9383-74d653b379e3"
CID_AUDIO_STREAM = "0b5cf52f-2b85-4863-890b-8844b64ecfe9"
CID_AUDIO_COMPONENT_CHAIN = "3cb131d1-d3c0-47ae-a19a-bdf75ea11674"
CID_AUDIO_CLIP = "b8830d03-de02-41ee-84ec-fe566dc70cd9"
CID_CLIP_CHANNEL_VECTOR_SERIALIZER = "333d203b-3a53-4195-8894-fc7523ff3dc7"
CID_CLIP_CHANNEL_SERIALIZER = "5c89aa7a-89a6-4483-becd-f2b1def42316"
CID_SECONDARY_CONTENT = "f9d004b5-cb04-4e2f-af6f-64fadc2c4be9"

# Audio placement-side
CID_AUDIO_CLIP_TRACK_ITEM = "064ec682-9ba6-11d5-af2d-9ca32c7d6164"
CID_LINK = "149d4ea5-a7d4-4b34-9bb7-16d783904bf2"

# Effect components
CID_VIDEO_FILTER_COMPONENT = "d10da199-beea-4dd1-b941-ed3a78766d50"
CID_VIDEO_COMPONENT_PARAM = "fe47129e-6c94-4fc0-95d5-c056a517aaf3"
CID_VIDEO_COMPONENT_PARAM_BOOL = "cc12343e-f113-4d3b-ae05-b287db77d461"  # bool
CID_VIDEO_COMPONENT_PARAM_CLAMPED = "a4ff2d6e-7ac2-44f8-9d52-17d9ca50e542"  # clamped float (anti-flicker)
CID_POINT_COMPONENT_PARAM = "ca81d347-309b-44d2-acc7-1c572efb973c"
