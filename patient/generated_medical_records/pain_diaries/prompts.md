# Prompts that generated these pain diaries

## Prompt 1
Here is an example pain diary entry in JSON format. Generate 10. diaries, matching this schema, that meet the following criteria:

1. The patient_id is 4403cbc3-78eb-fbe6-e5c5-bee837f31ea9
2. The pain entries should take place on 10 consecutive days, the last one being today's date.
3. Their pain level, sleep quality, and mood should get steadily worse over the 10 days.


 {
    "patient_id": "1ed62ea4-aa53-4a9d-8749-4782a84c4f58",
    "timestamp": "2025-07-07T09:45:54.422598",
    "pain_level": 4,
    "pain_location": "abdomen",
    "description": "sharp and sudden pain",
    "medications_taken": [
      "oxycodone",
      "ibuprofen"
    ],
    "associated_symptoms": [
      "dizziness"
    ],
    "mood": "frustrated",
    "sleep_quality": "poor",
    "activity_level": "bedridden"
  },

## Prompt 2
Do the same thing, except with the following changes:
1. patient_id is 29244161-9d02-b8b6-20cc-350f53ffe7a1
2. Same as before
3. Their pain, sleep quality, and mood should stay roughly the same. It can bounce around a little, each value doesn't have to be identical, but it should portray someone who's not overall getting better or worse

## Prompt 3
OK, doing the same thing again, except with these changes:

1. patient_id is f420e6d4-55db-974f-05cb-52d06375b65f
2. Same as above
3. The patient's pain, sleep quality, and mood are stedaily improving. The diaries should read as someone who's feeling better each day

