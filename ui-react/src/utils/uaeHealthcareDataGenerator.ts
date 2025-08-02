import { Member, ChronicCondition, CareGap, InterventionRecommendation } from '../types/healthcare';

// UAE-specific data pools
const UAE_EMIRATES = [
  'Dubai', 'Abu Dhabi', 'Sharjah', 'Ajman', 'Umm Al Quwain', 'Ras Al Khaimah', 'Fujairah'
];

const UAE_CITIES = {
  'Dubai': ['Dubai', 'Deira', 'Bur Dubai', 'Jumeirah', 'Downtown Dubai', 'Dubai Marina', 'Business Bay'],
  'Abu Dhabi': ['Abu Dhabi', 'Al Ain', 'Madinat Zayed', 'Ruwais', 'Liwa', 'Sweihan'],
  'Sharjah': ['Sharjah', 'Kalba', 'Khor Fakkan', 'Dibba Al-Hisn'],
  'Ajman': ['Ajman', 'Masfout'],
  'Umm Al Quwain': ['Umm Al Quwain'],
  'Ras Al Khaimah': ['Ras Al Khaimah', 'Julfar'],
  'Fujairah': ['Fujairah', 'Dibba Al-Fujairah', 'Masafi']
};

const ARABIC_FIRST_NAMES_MALE = [
  'Ahmed', 'Mohammed', 'Ali', 'Omar', 'Khalid', 'Abdullah', 'Hassan', 'Ibrahim', 'Youssef', 'Saeed',
  'Rashid', 'Sultan', 'Hamad', 'Majed', 'Faisal', 'Tariq', 'Nasser', 'Salim', 'Jamal', 'Fahad',
  'Mansour', 'Badr', 'Zayed', 'Humaid', 'Obaid', 'Saud', 'Nawaf', 'Rashed', 'Marwan', 'Adnan'
];

const ARABIC_FIRST_NAMES_FEMALE = [
  'Fatima', 'Aisha', 'Maryam', 'Khadija', 'Zainab', 'Huda', 'Noor', 'Salma', 'Layla', 'Amina',
  'Noura', 'Sara', 'Hind', 'Moza', 'Sheikha', 'Asma', 'Reem', 'Latifa', 'Mariam', 'Ayesha',
  'Shamma', 'Maitha', 'Meera', 'Dana', 'Lina', 'Dina', 'Rana', 'Hessa', 'Maha', 'Nadine'
];

const EXPATRIATE_FIRST_NAMES_MALE = [
  'John', 'Michael', 'David', 'James', 'Robert', 'William', 'Richard', 'Thomas', 'Christopher', 'Daniel',
  'Raj', 'Suresh', 'Vijay', 'Amit', 'Ravi', 'Kumar', 'Arif', 'Sanjay', 'Ashraf', 'Imran',
  'Jose', 'Antonio', 'Carlos', 'Luis', 'Fernando', 'Ricardo', 'Manuel', 'Eduardo', 'Francisco', 'Mario'
];

const EXPATRIATE_FIRST_NAMES_FEMALE = [
  'Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica', 'Sarah', 'Karen',
  'Priya', 'Sunita', 'Rekha', 'Kavya', 'Anita', 'Deepa', 'Fatima', 'Zara', 'Nadia', 'Samira',
  'Maria', 'Carmen', 'Rosa', 'Ana', 'Isabel', 'Teresa', 'Sofia', 'Lucia', 'Elena', 'Cristina'
];

const ARABIC_FAMILY_NAMES = [
  'Al Mansouri', 'Al Maktoum', 'Al Nahyan', 'Al Qasimi', 'Al Nuaimi', 'Al Sharqi', 'Al Mualla',
  'Al Mazrouei', 'Al Kaabi', 'Al Shamsi', 'Al Zaabi', 'Al Marri', 'Al Suwaidi', 'Al Hashemi',
  'Al Blooshi', 'Al Dhaheri', 'Al Marzooqi', 'Al Mansoori', 'Al Ketbi', 'Al Shehhi',
  'Al Hosani', 'Al Ameri', 'Al Bastaki', 'Al Falasi', 'Al Ghurair', 'Al Habtoor', 'Al Jaber',
  'Al Owais', 'Al Tayer', 'Al Futtaim', 'Bin Sulayem', 'Bin Hendi', 'Bin Lahej', 'Bin Mejren'
];

const EXPATRIATE_FAMILY_NAMES = [
  'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez',
  'Sharma', 'Patel', 'Singh', 'Kumar', 'Gupta', 'Agarwal', 'Verma', 'Shah', 'Jain', 'Mehta',
  'Khan', 'Ahmed', 'Ali', 'Hassan', 'Hussein', 'Rahman', 'Malik', 'Qureshi', 'Sheikh', 'Siddiqui',
  'Gonzalez', 'Lopez', 'Perez', 'Sanchez', 'Ramirez', 'Torres', 'Flores', 'Rivera', 'Gomez', 'Diaz'
];

const NATIONALITIES = [
  'UAE', 'Indian', 'Pakistani', 'Bangladeshi', 'Filipino', 'Egyptian', 'Syrian', 'Lebanese', 'Jordanian',
  'British', 'American', 'Canadian', 'Australian', 'German', 'French', 'Italian', 'Spanish',
  'South African', 'Ethiopian', 'Nigerian', 'Sudanese', 'Iranian', 'Afghan', 'Sri Lankan', 'Nepalese'
];

const INSURANCE_PROVIDERS = [
  'Dubai Health Insurance Company (Saada)',
  'Abu Dhabi Health Services Company (ADHS)',
  'DAMAN National Health Insurance Company',
  'Oman Insurance Company',
  'AXA Gulf',
  'MetLife Alico',
  'Orient Insurance Company',
  'Al Buhaira National Insurance Company',
  'Emirates Insurance Company',
  'Al Sagr National Insurance Company',
  'Watania International Holding',
  'Ras Al Khaimah National Insurance Company',
  'Arabia Insurance Company',
  'National General Insurance Company',
  'Sharjah Insurance Company'
];

const PLAN_TYPES = [
  'Essential', 'Enhanced', 'Comprehensive', 'Premium', 'Gold Plus', 'Platinum',
  'Silver', 'Bronze', 'Executive', 'Family Plus', 'Individual Basic', 'Corporate Elite'
];

const CHRONIC_CONDITIONS = [
  {
    condition: 'Type 2 Diabetes Mellitus',
    icdCode: 'E11.9',
    medications: ['Metformin', 'Insulin glargine', 'Empagliflozin', 'Sitagliptin'],
    severity: ['mild', 'moderate', 'severe'] as const
  },
  {
    condition: 'Essential Hypertension',
    icdCode: 'I10',
    medications: ['Amlodipine', 'Lisinopril', 'Losartan', 'Hydrochlorothiazide'],
    severity: ['mild', 'moderate'] as const
  },
  {
    condition: 'Hyperlipidemia',
    icdCode: 'E78.5',
    medications: ['Atorvastatin', 'Rosuvastatin', 'Simvastatin'],
    severity: ['mild', 'moderate'] as const
  },
  {
    condition: 'Bronchial Asthma',
    icdCode: 'J45.9',
    medications: ['Salbutamol', 'Fluticasone', 'Montelukast', 'Theophylline'],
    severity: ['mild', 'moderate', 'severe'] as const
  },
  {
    condition: 'Chronic Kidney Disease',
    icdCode: 'N18.6',
    medications: ['Furosemide', 'Calcium carbonate', 'Erythropoietin'],
    severity: ['moderate', 'severe'] as const
  },
  {
    condition: 'Coronary Artery Disease',
    icdCode: 'I25.10',
    medications: ['Clopidogrel', 'Atorvastatin', 'Metoprolol', 'Aspirin'],
    severity: ['moderate', 'severe'] as const
  },
  {
    condition: 'Chronic Obstructive Pulmonary Disease',
    icdCode: 'J44.1',
    medications: ['Tiotropium', 'Salbutamol', 'Prednisolone'],
    severity: ['moderate', 'severe'] as const
  },
  {
    condition: 'Rheumatoid Arthritis',
    icdCode: 'M06.9',
    medications: ['Methotrexate', 'Sulfasalazine', 'Hydroxychloroquine'],
    severity: ['mild', 'moderate', 'severe'] as const
  }
];

const ALLERGIES = [
  { allergen: 'Penicillin', reactions: ['Rash', 'Anaphylaxis', 'Hives'] },
  { allergen: 'Sulfonamides', reactions: ['Skin reaction', 'Stevens-Johnson syndrome'] },
  { allergen: 'Shellfish', reactions: ['Anaphylaxis', 'Hives', 'Swelling'] },
  { allergen: 'Peanuts', reactions: ['Anaphylaxis', 'Respiratory distress'] },
  { allergen: 'Latex', reactions: ['Contact dermatitis', 'Respiratory symptoms'] },
  { allergen: 'Iodine contrast', reactions: ['Anaphylaxis', 'Nausea'] },
  { allergen: 'NSAIDs', reactions: ['GI bleeding', 'Bronchospasm'] },
  { allergen: 'Aspirin', reactions: ['Asthma exacerbation', 'GI upset'] }
];

const HEALTHCARE_PROVIDERS = [
  'Emirates Hospital', 'Dubai Hospital', 'Sheikh Khalifa Medical City', 'Cleveland Clinic Abu Dhabi',
  'American Hospital Dubai', 'Mediclinic City Hospital', 'Saudi German Hospital',
  'Zulekha Hospital', 'NMC Royal Hospital', 'Aster Hospital', 'Burjeel Hospital',
  'Prime Healthcare Group', 'Canadian Specialist Hospital', 'Al Zahra Hospital',
  'Dr. Sulaiman Al Habib Hospital', 'King\'s College Hospital London', 'Moorfields Eye Hospital',
  'Great Ormond Street Hospital', 'International Modern Hospital', 'Life Care Hospital'
];

// Utility functions
const getRandomElement = <T>(array: T[]): T => array[Math.floor(Math.random() * array.length)];

const getRandomElements = <T>(array: T[], count: number): T[] => {
  const shuffled = [...array].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
};

const generateEmiratesId = (): string => {
  const year = Math.floor(Math.random() * 30) + 1970; // Born between 1970-2000
  const sequence = Math.floor(Math.random() * 10000000).toString().padStart(7, '0');
  const checkDigit = Math.floor(Math.random() * 10);
  return `784-${year}-${sequence}-${checkDigit}`;
};

const generatePhone = (): string => {
  const codes = ['50', '52', '54', '55', '56', '58'];
  const code = getRandomElement(codes);
  const number = Math.floor(Math.random() * 10000000).toString().padStart(7, '0');
  return `+971${code}${number}`;
};

const generatePolicyNumber = (provider: string): string => {
  const abbreviations: { [key: string]: string } = {
    'Dubai Health Insurance Company (Saada)': 'SAADA',
    'Abu Dhabi Health Services Company (ADHS)': 'ADHS',
    'DAMAN National Health Insurance Company': 'DAMAN',
    'Oman Insurance Company': 'OIC',
    'AXA Gulf': 'AXA',
    'MetLife Alico': 'MET'
  };

  const abbr = abbreviations[provider] || 'INS';
  const number = Math.floor(Math.random() * 1000000000).toString().padStart(9, '0');
  return `${abbr}-${number}`;
};

const generateDateOfBirth = (minAge: number = 18, maxAge: number = 80): string => {
  const today = new Date();
  const birthYear = today.getFullYear() - (minAge + Math.floor(Math.random() * (maxAge - minAge)));
  const birthMonth = Math.floor(Math.random() * 12);
  const birthDay = Math.floor(Math.random() * 28) + 1; // Avoid month-end issues

  return new Date(birthYear, birthMonth, birthDay).toISOString().split('T')[0];
};

const generateRecentDate = (daysBack: number = 365): string => {
  const today = new Date();
  const pastDate = new Date(today.getTime() - Math.random() * daysBack * 24 * 60 * 60 * 1000);
  return pastDate.toISOString();
};

const generateCosts = () => {
  const totalCosts = Math.floor(Math.random() * 50000) + 5000; // 5k to 55k AED
  const memberPaid = Math.floor(totalCosts * (0.1 + Math.random() * 0.3)); // 10-40%
  const planPaid = totalCosts - memberPaid;
  const deductible = Math.floor(Math.random() * 3000) + 500; // 500-3500 AED
  const deductibleMet = Math.min(deductible, memberPaid);

  return {
    totalCosts,
    memberPaid,
    planPaid,
    deductibleMet,
    outOfPocketMet: memberPaid
  };
};

// Main generator functions
export const generateMember = (isEmirati: boolean = Math.random() < 0.15): Member => {
  const gender = getRandomElement(['male', 'female'] as const);
  const dateOfBirth = generateDateOfBirth();
  const emirate = getRandomElement(UAE_EMIRATES);
  const city = getRandomElement(UAE_CITIES[emirate]);

  let firstName: string;
  let lastName: string;
  let nationality: string;

  if (isEmirati) {
    firstName = gender === 'male'
      ? getRandomElement(ARABIC_FIRST_NAMES_MALE)
      : getRandomElement(ARABIC_FIRST_NAMES_FEMALE);
    lastName = getRandomElement(ARABIC_FAMILY_NAMES);
    nationality = 'UAE';
  } else {
    const nationalityChoice = getRandomElement(NATIONALITIES.filter(n => n !== 'UAE'));
    nationality = nationalityChoice;

    if (['Indian', 'Pakistani', 'Bangladeshi'].includes(nationality)) {
      firstName = gender === 'male'
        ? getRandomElement([...ARABIC_FIRST_NAMES_MALE, ...EXPATRIATE_FIRST_NAMES_MALE])
        : getRandomElement([...ARABIC_FIRST_NAMES_FEMALE, ...EXPATRIATE_FIRST_NAMES_FEMALE]);
    } else {
      firstName = gender === 'male'
        ? getRandomElement(EXPATRIATE_FIRST_NAMES_MALE)
        : getRandomElement(EXPATRIATE_FIRST_NAMES_FEMALE);
    }

    lastName = Math.random() < 0.3 && ['Pakistani', 'Egyptian', 'Syrian'].includes(nationality)
      ? getRandomElement(ARABIC_FAMILY_NAMES)
      : getRandomElement(EXPATRIATE_FAMILY_NAMES);
  }

  const fullName = `${firstName} ${lastName}`;
  const email = `${firstName.toLowerCase()}.${lastName.toLowerCase().replace(/\s+/g, '')}@email.com`;
  const provider = getRandomElement(INSURANCE_PROVIDERS);
  const planType = getRandomElement(PLAN_TYPES);
  const policyNumber = generatePolicyNumber(provider);

  // Generate chronic conditions (higher probability for older people)
  const age = Math.floor((new Date().getTime() - new Date(dateOfBirth).getTime()) / (1000 * 60 * 60 * 24 * 365.25));
  const conditionCount = age > 50 ? Math.floor(Math.random() * 3) + 1 : Math.floor(Math.random() * 2);
  const selectedConditions = getRandomElements(CHRONIC_CONDITIONS, conditionCount);

  const chronicConditions: ChronicCondition[] = selectedConditions.map((conditionTemplate, index) => ({
    id: `condition-${index + 1}`,
    condition: conditionTemplate.condition,
    icdCode: conditionTemplate.icdCode,
    diagnosisDate: generateRecentDate(365 * 5), // Within last 5 years
    severity: getRandomElement(conditionTemplate.severity),
    status: getRandomElement(['active', 'chronic'] as const),
    managingProvider: getRandomElement(HEALTHCARE_PROVIDERS),
    medications: getRandomElements(conditionTemplate.medications, Math.floor(Math.random() * 3) + 1),
    lastReview: generateRecentDate(180) // Within last 6 months
  }));

  // Generate allergies
  const allergyCount = Math.floor(Math.random() * 3); // 0-2 allergies
  const selectedAllergies = getRandomElements(ALLERGIES, allergyCount);
  const allergies = selectedAllergies.map(allergyTemplate => ({
    allergen: allergyTemplate.allergen,
    severity: getRandomElement(['mild', 'moderate', 'severe'] as const),
    reaction: getRandomElement(allergyTemplate.reactions)
  }));

  // Generate cost utilization
  const yearToDate = generateCosts();
  const monthlyTrends = Array.from({ length: 12 }, (_, i) => ({
    month: `2024-${(i + 1).toString().padStart(2, '0')}`,
    totalCosts: Math.floor(Math.random() * 5000) + 500,
    visits: Math.floor(Math.random() * 5),
    prescriptions: Math.floor(Math.random() * 10)
  }));

  const topCategories = [
    { category: 'Medications', amount: yearToDate.totalCosts * 0.4, percentage: 40 },
    { category: 'Outpatient Visits', amount: yearToDate.totalCosts * 0.3, percentage: 30 },
    { category: 'Laboratory Tests', amount: yearToDate.totalCosts * 0.15, percentage: 15 },
    { category: 'Imaging', amount: yearToDate.totalCosts * 0.1, percentage: 10 },
    { category: 'Emergency Care', amount: yearToDate.totalCosts * 0.05, percentage: 5 }
  ];

  // Calculate risk score based on age, conditions, and costs
  let riskScore = 20; // Base score
  riskScore += Math.min((age - 30) * 0.5, 30); // Age factor
  riskScore += chronicConditions.length * 15; // Condition count
  riskScore += chronicConditions.filter(c => c.severity === 'severe').length * 10; // Severe conditions
  riskScore += Math.min(yearToDate.totalCosts / 1000, 25); // Cost factor
  riskScore = Math.min(Math.max(riskScore, 10), 95); // Clamp between 10-95

  const memberId = `MBR-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
  const createdAt = generateRecentDate(365 * 2);

  return {
    id: memberId,
    emiratesId: generateEmiratesId(),
    demographics: {
      firstName,
      lastName,
      fullName,
      dateOfBirth,
      gender,
      nationality,
      preferredLanguage: isEmirati ? 'Arabic' : 'English',
      maritalStatus: getRandomElement(['single', 'married', 'divorced'] as const)
    },
    contact: {
      phone: generatePhone(),
      alternativePhone: Math.random() < 0.3 ? generatePhone() : undefined,
      email,
      address: {
        street: `${Math.floor(Math.random() * 999) + 1} ${getRandomElement(['Al Wasl', 'Sheikh Zayed', 'Jumeirah', 'Al Khaleej', 'Al Mankhool'])} Road`,
        city,
        emirate,
        country: 'UAE',
        postalCode: Math.floor(Math.random() * 99999).toString().padStart(5, '0')
      },
      emergencyContact: {
        name: `${getRandomElement(gender === 'male' ? ARABIC_FIRST_NAMES_FEMALE : ARABIC_FIRST_NAMES_MALE)} ${lastName}`,
        relationship: getRandomElement(['Spouse', 'Parent', 'Sibling', 'Child']),
        phone: generatePhone()
      }
    },
    insurance: {
      provider,
      policyNumber,
      groupNumber: Math.random() < 0.7 ? `GRP-${Math.floor(Math.random() * 10000)}` : undefined,
      planType,
      effectiveDate: generateRecentDate(365).split('T')[0],
      expirationDate: new Date(new Date().getFullYear() + 1, 11, 31).toISOString().split('T')[0],
      deductible: Math.floor(Math.random() * 3000) + 500,
      coPayment: getRandomElement([10, 15, 20, 25]),
      outOfPocketMax: Math.floor(Math.random() * 10000) + 5000,
      benefitYear: '2024',
      status: getRandomElement(['active', 'active', 'active', 'suspended'] as const) // 75% active
    },
    medicalHistory: {
      allergies,
      chronicConditions,
      surgicalHistory: [], // Can be extended later
      familyHistory: [] // Can be extended later
    },
    costUtilization: {
      yearToDate,
      monthlyTrends,
      topCategories
    },
    recentRequests: [], // Can be populated with ProcessingRequest objects
    riskScore: Math.round(riskScore),
    lastActivity: generateRecentDate(30),
    createdAt,
    updatedAt: generateRecentDate(7)
  };
};

export const generateMembers = (count: number, emiratiPercentage: number = 0.15): Member[] => {
  const members: Member[] = [];
  const emiratiCount = Math.floor(count * emiratiPercentage);

  // Generate Emirati members
  for (let i = 0; i < emiratiCount; i++) {
    members.push(generateMember(true));
  }

  // Generate expatriate members
  for (let i = emiratiCount; i < count; i++) {
    members.push(generateMember(false));
  }

  return members;
};

export const generateCareGapsForMember = (member: Member): CareGap[] => {
  const gaps: CareGap[] = [];
  const today = new Date();

  // Check each chronic condition for care gaps
  member.medicalHistory.chronicConditions.forEach((condition, index) => {
    const lastReview = new Date(condition.lastReview);
    const daysSinceReview = Math.floor((today.getTime() - lastReview.getTime()) / (1000 * 60 * 60 * 24));

    // Diabetes care gaps
    if (condition.condition.toLowerCase().includes('diabetes')) {
      if (daysSinceReview > 90) {
        gaps.push({
          id: `gap-hba1c-${index}`,
          memberId: member.id,
          type: 'chronic_care',
          category: 'HbA1c Testing',
          description: 'Quarterly HbA1c testing overdue for diabetes monitoring',
          recommendation: 'Schedule HbA1c laboratory test within 2 weeks',
          priority: daysSinceReview > 120 ? 'high' : 'medium',
          dueDate: new Date(today.getTime() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          status: 'open',
          evidenceBase: 'ADA Clinical Practice Guidelines - HbA1c testing every 3 months',
          potentialCostSaving: 8000,
          createdAt: today.toISOString(),
          updatedAt: today.toISOString()
        });
      }

      if (daysSinceReview > 365) {
        gaps.push({
          id: `gap-eye-${index}`,
          memberId: member.id,
          type: 'preventive',
          category: 'Diabetic Eye Exam',
          description: 'Annual comprehensive eye examination overdue',
          recommendation: 'Schedule ophthalmology consultation for diabetic retinopathy screening',
          priority: 'high',
          dueDate: new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          status: 'open',
          evidenceBase: 'ADA Clinical Practice Guidelines - Annual eye exams for all diabetic patients',
          potentialCostSaving: 15000,
          assignedProvider: getRandomElement(HEALTHCARE_PROVIDERS),
          createdAt: today.toISOString(),
          updatedAt: today.toISOString()
        });
      }
    }

    // Hypertension care gaps
    if (condition.condition.toLowerCase().includes('hypertension')) {
      if (daysSinceReview > 180) {
        gaps.push({
          id: `gap-bp-${index}`,
          memberId: member.id,
          type: 'chronic_care',
          category: 'Blood Pressure Monitoring',
          description: 'Regular blood pressure monitoring overdue',
          recommendation: 'Schedule follow-up appointment for blood pressure assessment',
          priority: daysSinceReview > 240 ? 'high' : 'medium',
          dueDate: new Date(today.getTime() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          status: 'open',
          evidenceBase: 'AHA/ACC Hypertension Guidelines - Regular monitoring required',
          potentialCostSaving: 25000,
          createdAt: today.toISOString(),
          updatedAt: today.toISOString()
        });
      }
    }
  });

  // Age-based preventive care
  const age = Math.floor((today.getTime() - new Date(member.demographics.dateOfBirth).getTime()) / (1000 * 60 * 60 * 24 * 365.25));

  if (age >= 50 && Math.random() < 0.7) {
    gaps.push({
      id: `gap-colonoscopy-${member.id}`,
      memberId: member.id,
      type: 'preventive',
      category: 'Colorectal Cancer Screening',
      description: 'Colorectal cancer screening due based on age',
      recommendation: 'Schedule colonoscopy or alternative screening method',
      priority: age >= 60 ? 'high' : 'medium',
      dueDate: new Date(today.getTime() + 60 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      status: 'open',
      evidenceBase: 'USPSTF Guidelines - Screening recommended ages 50-75',
      potentialCostSaving: 50000,
      createdAt: today.toISOString(),
      updatedAt: today.toISOString()
    });
  }

  // Medication adherence gaps
  if (member.medicalHistory.chronicConditions.length > 0 && Math.random() < 0.3) {
    const condition = getRandomElement(member.medicalHistory.chronicConditions);
    gaps.push({
      id: `gap-medication-${member.id}`,
      memberId: member.id,
      type: 'medication_adherence',
      category: 'Medication Refill Gap',
      description: `Potential medication adherence issue for ${condition.condition}`,
      recommendation: 'Contact member to review medication adherence and refill history',
      priority: 'urgent',
      dueDate: new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      status: 'open',
      evidenceBase: 'Medication adherence critical for chronic disease management',
      potentialCostSaving: 12000,
      createdAt: today.toISOString(),
      updatedAt: today.toISOString()
    });
  }

  return gaps;
};

export const searchMembers = (
  members: Member[],
  query: string,
  fuzzyThreshold: number = 50
): Member[] => {
  if (!query.trim()) return members;

  const fuzzyScore = (term: string, target: string): number => {
    if (!term || !target) return 0;

    term = term.toLowerCase();
    target = target.toLowerCase();

    if (target.includes(term)) return 100;

    let score = 0;
    let termIndex = 0;

    for (let i = 0; i < target.length && termIndex < term.length; i++) {
      if (target[i] === term[termIndex]) {
        score++;
        termIndex++;
      }
    }

    return (score / term.length) * 100;
  };

  return members.filter(member => {
    const searchFields = [
      member.demographics.fullName,
      member.demographics.firstName,
      member.demographics.lastName,
      member.emiratesId,
      member.contact.phone,
      member.contact.email,
      member.insurance.policyNumber,
      member.insurance.provider,
      member.contact.address.city,
      member.contact.address.emirate,
      member.demographics.nationality
    ];

    return searchFields.some(field =>
      field && fuzzyScore(query, field) >= fuzzyThreshold
    );
  });
};

// Export default sample data
export const SAMPLE_UAE_MEMBERS = generateMembers(100);
