/* Shared JSON contract for Gemini, browser imports and GitHub validation. */
window.goatAIContract = {
  "version": "goat-comparison-v2",
  "template": "oia-goat-comparison-v1",
  "metric_ids": [
    "career.starts",
    "career.titles",
    "career.wins",
    "career.podiums",
    "career.poles",
    "features.qualifying_position",
    "features.gap_to_pole",
    "features.start_score",
    "features.race_score",
    "features.metronome",
    "features.teammate_pace",
    "features.pit_race_gain"
  ],
  "domain_ids": [
    "career",
    "qualifying",
    "start",
    "progression",
    "pace",
    "pit_balance"
  ],
  "schema": {
    "type": "object",
    "properties": {
      "schema_version": {
        "type": "string",
        "enum": [
          "goat-comparison-v2"
        ]
      },
      "input_status": {
        "type": "string",
        "enum": [
          "complete",
          "incomplete"
        ]
      },
      "selected_drivers": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": [
            "__DRIVER__"
          ]
        },
        "minItems": "__COUNT__",
        "maxItems": "__COUNT__"
      },
      "context": {
        "type": "object",
        "properties": {
          "source_revision": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
          },
          "facts_period": {
            "type": "array",
            "items": {
              "type": "integer"
            },
            "minItems": 2,
            "maxItems": 2
          },
          "circuits": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1,
              "maxLength": 100
            },
            "minItems": 0,
            "maxItems": 100
          },
          "curve_years": {
            "type": "string",
            "enum": [
              "career",
              "calendar"
            ]
          }
        },
        "required": [
          "source_revision",
          "facts_period",
          "circuits",
          "curve_years"
        ],
        "additionalProperties": false
      },
      "summary": {
        "type": "string",
        "minLength": 1,
        "maxLength": 1600
      },
      "comparisons": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "driver": {
              "type": "string",
              "enum": [
                "__DRIVER__"
              ]
            },
            "strength": {
              "type": "string",
              "minLength": 1,
              "maxLength": 900
            },
            "limitation": {
              "type": "string",
              "minLength": 1,
              "maxLength": 900
            },
            "evidence": {
              "type": "array",
              "items": {
                "type": "string",
                "enum": [
                  "career.starts",
                  "career.titles",
                  "career.wins",
                  "career.podiums",
                  "career.poles",
                  "features.qualifying_position",
                  "features.gap_to_pole",
                  "features.start_score",
                  "features.race_score",
                  "features.metronome",
                  "features.teammate_pace",
                  "features.pit_race_gain"
                ]
              },
              "minItems": 0,
              "maxItems": 8
            }
          },
          "required": [
            "driver",
            "strength",
            "limitation",
            "evidence"
          ],
          "additionalProperties": false
        },
        "minItems": "__COUNT__",
        "maxItems": "__COUNT__"
      },
      "domains": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "string",
              "enum": [
                "career",
                "qualifying",
                "start",
                "progression",
                "pace",
                "pit_balance"
              ]
            },
            "included_in_verdict": {
              "type": "boolean"
            },
            "weight": {
              "type": "number",
              "minimum": 0,
              "maximum": 1
            },
            "leaders": {
              "type": "array",
              "items": {
                "type": "string",
                "enum": [
                  "__DRIVER__"
                ]
              },
              "minItems": 0,
              "maxItems": 4
            },
            "explanation": {
              "type": "string",
              "minLength": 1,
              "maxLength": 700
            }
          },
          "required": [
            "id",
            "included_in_verdict",
            "weight",
            "leaders",
            "explanation"
          ],
          "additionalProperties": false
        },
        "minItems": 6,
        "maxItems": 6
      },
      "winner": {
        "type": [
          "string",
          "null"
        ],
        "enum": [
          "__DRIVER__",
          null
        ]
      },
      "runner_up": {
        "type": [
          "string",
          "null"
        ],
        "enum": [
          "__DRIVER__",
          null
        ]
      },
      "conclusion": {
        "type": "string",
        "minLength": 1,
        "maxLength": 1600
      },
      "confidence": {
        "type": "string",
        "enum": [
          "low",
          "medium",
          "high"
        ]
      },
      "assumptions": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1,
          "maxLength": 700
        },
        "minItems": 1,
        "maxItems": 8
      },
      "limitations": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1,
          "maxLength": 700
        },
        "minItems": 1,
        "maxItems": 8
      },
      "infographic": {
        "type": "object",
        "properties": {
          "template": {
            "type": "string",
            "enum": [
              "oia-goat-comparison-v1"
            ]
          },
          "title": {
            "type": "string",
            "minLength": 1,
            "maxLength": 90
          },
          "subtitle": {
            "type": "string",
            "minLength": 1,
            "maxLength": 180
          },
          "metric_ids": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": [
                "career.starts",
                "career.titles",
                "career.wins",
                "career.podiums",
                "career.poles",
                "features.qualifying_position",
                "features.gap_to_pole",
                "features.start_score",
                "features.race_score",
                "features.metronome",
                "features.teammate_pace",
                "features.pit_race_gain"
              ]
            },
            "minItems": 4,
            "maxItems": 8
          },
          "takeaway": {
            "type": "string",
            "minLength": 1,
            "maxLength": 260
          }
        },
        "required": [
          "template",
          "title",
          "subtitle",
          "metric_ids",
          "takeaway"
        ],
        "additionalProperties": false
      },
      "ranking": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "driver": {
              "type": "string",
              "enum": [
                "__DRIVER__"
              ]
            },
            "position": {
              "type": [
                "integer",
                "null"
              ],
              "minimum": 1,
              "maximum": "__COUNT__"
            },
            "reason": {
              "type": "string",
              "minLength": 1,
              "maxLength": 500
            }
          },
          "required": [
            "driver",
            "position",
            "reason"
          ],
          "additionalProperties": false
        },
        "minItems": "__COUNT__",
        "maxItems": "__COUNT__"
      }
    },
    "required": [
      "schema_version",
      "input_status",
      "selected_drivers",
      "context",
      "summary",
      "comparisons",
      "domains",
      "winner",
      "runner_up",
      "conclusion",
      "confidence",
      "assumptions",
      "limitations",
      "infographic",
      "ranking"
    ],
    "additionalProperties": false
  },
  "quality_weights": {
    "career": 0.05,
    "qualifying": 0.2,
    "start": 0.15,
    "progression": 0.25,
    "pace": 0.3,
    "pit_balance": 0.05
  }
};
