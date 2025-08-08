// Medical specialty determination for UAE healthcare pre-authorization
// Uses GPT-4o-mini for cost-effective, intelligent specialty classification

enum MedicalSpecialty {
  Pediatric
  Diabetes  
  Cardiac
  Respiratory
  Oncology
  Orthopedic
  Nephrology
  Dermatology
  Neurology
  MentalHealth
  General
}

class PatientContext {
  age int?
  date_of_birth string?
  demographics map<string, string>?
}

class ServiceRequest {
  description string?
  code string?
  activity_code string?
  diagnosis_code string?
}

class MedicalHistory {
  labs string[]?
  medications string[]?
  claims string[]?
  conditions string[]?
}

function DetermineSpecialty(
  patient_context: PatientContext,
  services: ServiceRequest[],
  medical_history: MedicalHistory
) -> MedicalSpecialty {
  client CustomGPT4oMini
  prompt #"
    You are a medical specialty classifier for UAE healthcare pre-authorization system.
    
    Your task is to determine the most appropriate medical specialty based on:
    1. Patient demographics and age
    2. Requested medical services and procedures
    3. Patient's medical history and conditions
    
    CLASSIFICATION RULES:
    - If patient age < 18: Always return "Pediatric"
    - Otherwise, analyze the clinical context to determine the primary specialty
    
    SPECIALTY CATEGORIES:
    - Pediatric: Patients under 18 years
    - Diabetes: Diabetes management, insulin, HbA1c monitoring, glucose control, diabetic complications
    - Cardiac: Heart conditions, cardiovascular procedures, cardiac catheterization, cardiology
    - Respiratory: Lung conditions, asthma, COPD, respiratory therapy, pulmonology
    - Oncology: Cancer treatment, chemotherapy, radiation, tumor management
    - Orthopedic: Bone/joint conditions, orthopedic surgery, musculoskeletal disorders
    - Nephrology: Kidney conditions, renal failure, dialysis, nephrology
    - Dermatology: Skin conditions, dermatological treatments
    - Neurology: Neurological conditions, brain disorders, Parkinson's, epilepsy
    - MentalHealth: Psychiatric conditions, mental health treatment, psychology
    - General: Default for conditions not clearly fitting other specialties or multiple systems
    
    UAE CONTEXT:
    - Consider Arabic medical terminology and UAE healthcare standards
    - Account for eClaimLink (Dubai) and Shafafiya (Abu Dhabi) data formats
    - Focus on primary specialty for pre-authorization routing
    
    PATIENT CONTEXT:
    Age: {{ patient_context.age }}
    Date of Birth: {{ patient_context.date_of_birth }}
    Demographics: {{ patient_context.demographics }}
    
    REQUESTED SERVICES:
    {% for service in services %}
    - Description: {{ service.description }}
    - Code: {{ service.code }}
    - Activity Code: {{ service.activity_code }}
    - Diagnosis Code: {{ service.diagnosis_code }}
    {% endfor %}
    
    MEDICAL HISTORY:
    Recent Labs: {{ medical_history.labs }}
    Current Medications: {{ medical_history.medications }}
    Recent Claims: {{ medical_history.claims }}
    Medical Conditions: {{ medical_history.conditions }}
    
    Based on this information, determine the single most appropriate medical specialty.
    Consider the primary condition being treated and the main area of medical expertise required.
    
    Return only the specialty category (no explanation needed).
  "#
}



// Test cases for DetermineSpecialty BAML function
// Validates medical specialty classification accuracy

test TestPediatricCase {
  functions [DetermineSpecialty]
  args {
    patient_context {
      age 15
      date_of_birth "15/06/2009"
      demographics {
        "gender" "female"
        "nationality" "UAE"
      }
    }
    services [
      {
        description "Routine pediatric checkup and vaccination"
        code "99213"
        activity_code "PEDS_CHECKUP"
        diagnosis_code "Z00.129"
      }
    ]
    medical_history {
      labs ["Normal CBC", "Growth parameters within range"]
      medications []
      claims ["Previous vaccination records"]
      conditions []
    }
  }
}

test TestDiabetesCase {
  functions [DetermineSpecialty]
  args {
    patient_context {
      age 45
      date_of_birth "12/03/1979"
      demographics {
        "gender" "male"
        "nationality" "UAE"
      }
    }
    services [
      {
        description "HbA1c monitoring and diabetes management consultation"
        code "83036"
        activity_code "DIABETES_MGMT"
        diagnosis_code "E11.9"
      },
      {
        description "Insulin pump therapy evaluation"
        code "95251"
        activity_code "INSULIN_PUMP"
        diagnosis_code "E11.65"
      }
    ]
    medical_history {
      labs ["HbA1c: 8.2%", "Fasting glucose: 165 mg/dL"]
      medications ["Metformin 1000mg", "Insulin glargine"]
      claims ["Previous diabetes supplies", "CGM sensors"]
      conditions ["Type 2 Diabetes Mellitus"]
    }
  }
}

test TestCardiacCase {
  functions [DetermineSpecialty]
  args {
    patient_context {
      age 62
      date_of_birth "08/11/1962"
      demographics {
        "gender" "male"
        "nationality" "UAE"
      }
    }
    services [
      {
        description "Cardiac catheterization and coronary angiography"
        code "93458"
        activity_code "CARDIAC_CATH"
        diagnosis_code "I25.10"
      }
    ]
    medical_history {
      labs ["Troponin elevated", "CK-MB: 12 ng/mL"]
      medications ["Atorvastatin", "Metoprolol", "Aspirin"]
      claims ["Previous ECG", "Stress test"]
      conditions ["Coronary artery disease", "Hypertension"]
    }
  }
}

test TestRespiratoryCase {
  functions [DetermineSpecialty]
  args {
    patient_context {
      age 58
      date_of_birth "22/09/1966"
      demographics {
        "gender" "female"
        "nationality" "UAE"
      }
    }
    services [
      {
        description "Pulmonary function testing and COPD management"
        code "94010"
        activity_code "PFT_COPD"
        diagnosis_code "J44.1"
      }
    ]
    medical_history {
      labs ["ABG showing mild hypoxemia"]
      medications ["Albuterol", "Tiotropium", "Prednisolone"]
      claims ["Previous chest X-ray", "Spirometry"]
      conditions ["COPD", "Chronic bronchitis"]
    }
  }
}

test TestOncologyCase {
  functions [DetermineSpecialty]
  args {
    patient_context {
      age 52
      date_of_birth "17/04/1972"
      demographics {
        "gender" "female"
        "nationality" "UAE"
      }
    }
    services [
      {
        description "Chemotherapy administration - breast cancer treatment"
        code "96413"
        activity_code "CHEMO_ADMIN"
        diagnosis_code "C50.911"
      }
    ]
    medical_history {
      labs ["CA 15-3 elevated", "CBC with differential"]
      medications ["Doxorubicin", "Cyclophosphamide", "Ondansetron"]
      claims ["Previous biopsy", "CT staging"]
      conditions ["Invasive ductal carcinoma", "Stage IIIA breast cancer"]
    }
  }
}

test TestGeneralCase {
  functions [DetermineSpecialty]
  args {
    patient_context {
      age 35
      date_of_birth "10/07/1989"
      demographics {
        "gender" "male"
        "nationality" "UAE"
      }
    }
    services [
      {
        description "Annual comprehensive physical examination"
        code "99396"
        activity_code "ANNUAL_PHYSICAL"
        diagnosis_code "Z00.00"
      }
    ]
    medical_history {
      labs ["Complete metabolic panel - normal"]
      medications []
      claims ["Previous routine visits"]
      conditions []
    }
  }
}