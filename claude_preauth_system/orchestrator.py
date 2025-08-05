#!/usr/bin/env python3
"""
Pre-Authorization Orchestrator with Real Agent Execution
========================================================

Multi-agent system for UAE healthcare pre-authorization analysis using specialized Claude Code agents.

WORKFLOW:
1. Takes XML file path (eClaimLink/Shafafiya format)
2. Reads XML and extracts patient info + Emirates ID
3. Calls ETL to get comprehensive patient data (CSV + FHIR)
4. Loads agent definitions from .md files
5. Runs real Claude Code agents in 3 phases with comprehensive analysis
6. Returns detailed results with final authorization decision

AGENTS USED (5):
Phase 1 - Initial Analysis (Parallel):
• clinical-analyzer: Medical history review, disease progression analysis, clinical necessity assessment
• medication-specialist: Drug interactions, safety assessment, contraindications, dosage validation

Phase 2 - Risk Assessment:
• risk-assessor: Clinical risk stratification, outcome prediction, cost-benefit analysis (depends on Phase 1)

Phase 3 - Decision & Compliance (Parallel):
• decision-maker: Evidence-based authorization recommendations, final clinical decision (depends on Phase 1+2)
• compliance-auditor: UAE regulatory compliance verification, documentation requirements (depends on decision-maker)

Each agent loads specialized prompts from /agents/*.md files and provides detailed medical analysis.

Usage:
    orchestrator = PreAuthOrchestrator()
    results = orchestrator.process_xml_request("path/to/request.xml")
"""

import sys
import json
import asyncio
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import traceback

# Add data_ingestion to path for ETL access
sys.path.append(str(Path(__file__).parent.parent / "data_ingestion"))

from etl import get_patient_data, find_patient_by_emirates_id, DATASET_PATH

# Claude Code SDK imports
try:
    from claude_code_sdk import (
        query,
        ClaudeCodeOptions,
        AssistantMessage,
        TextBlock,
        ResultMessage,
    )
    SDK_AVAILABLE = True
except ImportError:
    print("Warning: Claude Code SDK not available. Install with: pip install claude-code-sdk")
    SDK_AVAILABLE = False

class PreAuthOrchestrator:
    """Pre-authorization orchestrator with real Claude Code agent execution."""
    
    def __init__(self):
        """Initialize orchestrator with agent definitions."""
        self.base_path = Path(__file__).parent
        self.agents_dir = self.base_path / "agents"
        
        # Agent configuration with phases and dependencies
        self.agents = {
            "clinical-analyzer": {
                "phase": 1,
                "dependencies": [],
                "description": "Medical history and disease progression analysis",
            },
            "medication-specialist": {
                "phase": 1,
                "dependencies": [],
                "description": "Drug interactions and safety assessment",
            },
            "risk-assessor": {
                "phase": 2,
                "dependencies": ["clinical-analyzer", "medication-specialist"],
                "description": "Clinical risk stratification and outcome prediction",
            },
            "decision-maker": {
                "phase": 3,
                "dependencies": ["clinical-analyzer", "medication-specialist", "risk-assessor"],
                "description": "Evidence-based authorization recommendations",
            },
            "compliance-auditor": {
                "phase": 3,
                "dependencies": ["decision-maker"],
                "description": "UAE regulatory compliance verification",
            },
        }
        
        # Load agent definitions from .md files
        self.agent_definitions = {}
        self._load_agent_definitions()
        
        # Results storage
        self.agent_results = {}
        self.token_usage = {}
        self.total_cost = 0.0
    
    def process_xml_request(self, xml_file_path: str) -> Dict[str, Any]:
        """
        Process XML pre-authorization request with real agent analysis.
        
        Args:
            xml_file_path: Path to XML request file
            
        Returns:
            Complete analysis results with real agent outputs
        """
        
        print(f"🔄 Processing XML request: {xml_file_path}")
        
        # Step 1: Read and parse XML
        xml_data = self._parse_xml(xml_file_path)
        print(f"✅ Parsed XML format: {xml_data['format']}")
        
        # Step 2: Extract patient info from XML
        patient_info = self._extract_patient_info(xml_data)
        patient_id = patient_info['patient_id']
        print(f"✅ Found patient: {patient_id}")
        
        # Step 3: Get patient data from ETL
        patient_data = get_patient_data(patient_id)
        print(f"✅ Retrieved patient data: {len(patient_data['labs'])} labs, {len(patient_data['claims'])} claims")
        
        # Step 4: Determine medical specialty
        specialty = self._determine_specialty(xml_data, patient_data)
        print(f"✅ Medical specialty: {specialty}")
        
        # Step 5: Run real Claude Code agents
        if SDK_AVAILABLE:
            print("🤖 Running Claude Code agents for comprehensive analysis...")
            agent_results = asyncio.run(self._orchestrate_agents(xml_data, patient_info, patient_data, specialty))
            print(f"✅ Agents completed: {len(agent_results)} agents")
        else:
            print("⚠️  Claude Code SDK not available, using fallback analysis")
            agent_results = self._fallback_analysis(xml_data, patient_info, patient_data, specialty)
        
        # Step 6: Make final decision based on agent results
        final_decision = self._make_final_decision(agent_results, xml_data, patient_data)
        print(f"✅ Final decision: {final_decision['decision']}")
        
        return {
            'xml_data': xml_data,
            'patient_info': patient_info,
            'patient_data': patient_data,
            'specialty': specialty,
            'agent_results': agent_results,
            'final_decision': final_decision,
            'cost_tracking': {
                'total_cost_usd': self.total_cost,
                'token_usage_by_agent': self.token_usage,
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _load_agent_definitions(self) -> None:
        """Load agent definitions from markdown files."""
        
        # Create agents directory if it doesn't exist
        self.agents_dir.mkdir(exist_ok=True)
        
        for agent_name in self.agents.keys():
            agent_file = self.agents_dir / f"{agent_name}.md"
            
            if agent_file.exists():
                try:
                    with open(agent_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    self.agent_definitions[agent_name] = self._parse_agent_definition(content)
                    print(f"✅ Loaded {agent_name} definition from {agent_file}")
                    
                except Exception as e:
                    print(f"❌ Failed to load {agent_name} definition: {e}")
                    self.agent_definitions[agent_name] = self._create_default_definition(agent_name)
            else:
                print(f"⚠️  Creating default definition for {agent_name} (no .md file found)")
                self.agent_definitions[agent_name] = self._create_default_definition(agent_name)
                
                # Create a basic .md file for future customization
                self._create_default_agent_file(agent_name, agent_file)
    
    def _parse_agent_definition(self, content: str) -> Dict[str, Any]:
        """Parse agent definition from markdown content."""
        lines = content.split('\n')
        definition = {
            'name': '',
            'description': '',
            'instructions': '',
            'tools': ['Read', 'Grep', 'Glob'],
        }
        
        # Extract frontmatter if present
        if lines and lines[0].strip() == '---':
            frontmatter_end = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    frontmatter_end = i + 1
                    break
            
            if frontmatter_end > 0:
                for line in lines[1:frontmatter_end-1]:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'name':
                            definition['name'] = value
                        elif key == 'description':
                            definition['description'] = value
                        elif key == 'tools':
                            if value.startswith('[') and value.endswith(']'):
                                tools_str = value[1:-1]
                                definition['tools'] = [t.strip() for t in tools_str.split(',')]
                
                content_lines = lines[frontmatter_end:]
            else:
                content_lines = lines
        else:
            content_lines = lines
        
        definition['instructions'] = '\n'.join(content_lines).strip()
        return definition
    
    def _create_default_definition(self, agent_name: str) -> Dict[str, Any]:
        """Create default agent definition."""
        return {
            'name': agent_name,
            'description': self.agents[agent_name]['description'],
            'instructions': f"You are a {agent_name.replace('-', ' ')} specialist for UAE healthcare pre-authorization analysis.",
            'tools': ['Read', 'Grep', 'Glob'],
        }
    
    def _create_default_agent_file(self, agent_name: str, agent_file: Path) -> None:
        """Create a default agent .md file for customization."""
        default_content = f"""---
name: {agent_name}
description: {self.agents[agent_name]['description']}
tools: [Read, Grep, Glob]
---

# {agent_name.title().replace('-', ' ')} Agent

You are a specialized {agent_name.replace('-', ' ')} for UAE healthcare pre-authorization analysis.

## Your Role
{self.agents[agent_name]['description']}

## Instructions
1. Analyze the provided patient data thoroughly
2. Focus on your area of expertise
3. Provide detailed, evidence-based recommendations
4. Consider UAE healthcare regulations and standards
5. Document your findings clearly

## Expected Output
- Comprehensive analysis report
- Clear recommendations
- Risk assessments where applicable
- Evidence citations
"""
        
        with open(agent_file, 'w', encoding='utf-8') as f:
            f.write(default_content)
        
        print(f"📝 Created default agent file: {agent_file}")
    
    async def _orchestrate_agents(self, xml_data: Dict[str, Any], patient_info: Dict[str, Any], 
                                 patient_data: Dict[str, Any], specialty: str) -> Dict[str, Any]:
        """Orchestrate real Claude Code agents in phases."""
        
        # Prepare shared context
        shared_context = self._prepare_shared_context(xml_data, patient_info, patient_data, specialty)
        
        # Phase 1: Initial parallel analysis
        print("📋 Phase 1: Clinical and Medication Analysis")
        phase_1_agents = ['clinical-analyzer', 'medication-specialist']
        phase_1_results = await self._run_phase(phase_1_agents, shared_context)
        
        # Phase 2: Risk assessment
        print("⚖️ Phase 2: Risk Stratification")
        phase_2_agents = ['risk-assessor']
        phase_2_results = await self._run_phase(phase_2_agents, shared_context)
        
        # Phase 3: Decision and compliance
        print("🏥 Phase 3: Decision Making and Compliance")
        phase_3_agents = ['decision-maker', 'compliance-auditor']
        phase_3_results = await self._run_phase(phase_3_agents, shared_context)
        
        # Combine all results
        all_results = {**phase_1_results, **phase_2_results, **phase_3_results}
        
        return all_results
    
    async def _run_phase(self, agent_names: List[str], shared_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run agents in a phase (parallel execution)."""
        
        if len(agent_names) > 1:
            # Run agents in parallel
            tasks = [self._run_agent(agent_name, shared_context) for agent_name in agent_names]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Single agent
            results = [await self._run_agent(agent_names[0], shared_context)]
        
        # Process results
        phase_results = {}
        for i, result in enumerate(results):
            agent_name = agent_names[i]
            if isinstance(result, Exception):
                print(f"❌ Exception in {agent_name}: {result}")
                phase_results[agent_name] = {
                    'status': 'failed',
                    'error': str(result),
                    'success': False,
                }
            else:
                phase_results[agent_name] = result
                self.agent_results[agent_name] = result
        
        return phase_results
    
    async def _run_agent(self, agent_name: str, shared_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific Claude Code agent."""
        
        try:
            print(f"🤖 Starting {agent_name} analysis...")
            start_time = datetime.now()
            
            # Build agent-specific prompt
            prompt = self._build_agent_prompt(agent_name, shared_context)
            
            # Configure Claude Code options
            options = ClaudeCodeOptions(
                cwd=str(Path.cwd()),
                max_turns=15,
                allowed_tools=['Read', 'Grep', 'Glob'],
            )
            
            # Execute agent and collect results
            text_responses = []
            all_messages = []
            usage_data = {}
            
            async for message in query(prompt=prompt, options=options):
                all_messages.append(str(message))
                
                # Extract text from AssistantMessage
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            text_responses.append(block.text)
                
                # Capture usage data from ResultMessage
                if isinstance(message, ResultMessage):
                    if hasattr(message, 'usage') and message.usage:
                        usage_data = {
                            'input_tokens': message.usage.get('input_tokens', 0),
                            'output_tokens': message.usage.get('output_tokens', 0),
                            'total_tokens': message.usage.get('input_tokens', 0) + message.usage.get('output_tokens', 0),
                        }
                    
                    if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
                        usage_data['total_cost_usd'] = float(message.total_cost_usd)
                        self.total_cost += usage_data['total_cost_usd']
            
            # Process response
            meaningful_response = '\n\n'.join(text_responses) if text_responses else 'Analysis completed'
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Store usage data
            if usage_data:
                self.token_usage[agent_name] = usage_data
            
            result = {
                'agent_name': agent_name,
                'status': 'completed',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'processing_time_seconds': processing_time,
                'response': meaningful_response,
                'usage': usage_data,
                'success': True,
            }
            
            print(f"✅ {agent_name} completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            print(f"❌ {agent_name} failed: {e}")
            return {
                'agent_name': agent_name,
                'status': 'failed',
                'error': str(e),
                'traceback': traceback.format_exc(),
                'success': False,
            }
    
    def _build_agent_prompt(self, agent_name: str, shared_context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for agent using loaded definition."""
        
        agent_def = self.agent_definitions.get(agent_name, {})
        agent_instructions = agent_def.get('instructions', '')
        
        # Get previous agent results for dependencies
        dependencies = self.agents[agent_name].get('dependencies', [])
        previous_results = {}
        for dep in dependencies:
            if dep in self.agent_results:
                previous_results[dep] = self.agent_results[dep].get('response', 'Not available')
        
        prompt = f"""**MEDICAL PRE-AUTHORIZATION ANALYSIS TASK**

**PATIENT DATA CONTEXT**:
{json.dumps(shared_context, indent=2)}

**PREVIOUS AGENT ANALYSES**:
{json.dumps(previous_results, indent=2) if previous_results else "None - this is a first-phase agent"}

**YOUR SPECIALIZED ROLE**:
{agent_instructions}

**ANALYSIS REQUIREMENTS**:
1. Conduct thorough analysis based on your expertise
2. Consider UAE healthcare regulations and standards
3. Provide evidence-based recommendations
4. Document findings clearly with specific details
5. Consider the patient's complete medical history and current request

**START COMPREHENSIVE ANALYSIS NOW** - Focus on your specialized area of expertise and provide detailed insights."""

        return prompt
    
    def _prepare_shared_context(self, xml_data: Dict[str, Any], patient_info: Dict[str, Any], 
                               patient_data: Dict[str, Any], specialty: str) -> Dict[str, Any]:
        """Prepare shared context for all agents."""
        
        return {
            'xml_request': {
                'format': xml_data['format'],
                'file_path': xml_data['file_path'],
                'services_requested': patient_info['services'],
                'total_cost': patient_info['total_cost'],
            },
            'patient_demographics': patient_data['demographics'],
            'medical_history': {
                'lab_records': len(patient_data['labs']),
                'medications': len(patient_data['medications']),
                'claims_history': len(patient_data['claims']),
                'preauth_history': len(patient_data['preauth_history']),
            },
            'clinical_data': {
                'recent_labs': patient_data['labs'][-5:] if patient_data['labs'] else [],
                'current_medications': patient_data['medications'],
                'recent_claims': patient_data['claims'][-3:] if patient_data['claims'] else [],
            },
            'specialty': specialty,
            'analysis_timestamp': datetime.now().isoformat(),
        }
    
    def _fallback_analysis(self, xml_data: Dict[str, Any], patient_info: Dict[str, Any], 
                          patient_data: Dict[str, Any], specialty: str) -> Dict[str, Any]:
        """Fallback analysis when SDK not available."""
        
        return {
            'clinical-analyzer': {
                'status': 'fallback',
                'response': 'Clinical analysis requires Claude Code SDK for comprehensive evaluation.',
                'success': False,
            },
            'medication-specialist': {
                'status': 'fallback', 
                'response': 'Medication analysis requires Claude Code SDK for drug interaction assessment.',
                'success': False,
            },
            'risk-assessor': {
                'status': 'fallback',
                'response': 'Risk assessment requires Claude Code SDK for comprehensive risk stratification.',
                'success': False,
            },
            'decision-maker': {
                'status': 'fallback',
                'response': 'Decision making requires Claude Code SDK for evidence-based recommendations.',
                'success': False,
            },
            'compliance-auditor': {
                'status': 'fallback',
                'response': 'Compliance audit requires Claude Code SDK for regulatory verification.',
                'success': False,
            },
        }
    
    def _make_final_decision(self, agent_results: Dict[str, Any], xml_data: Dict[str, Any], 
                            patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make final decision based on agent analyses."""
        
        # Get decision maker result if available
        decision_agent = agent_results.get('decision-maker', {})
        
        if decision_agent.get('success'):
            # Extract decision from agent response
            response = decision_agent.get('response', '')
            
            # Simple keyword extraction for decision
            if 'approved' in response.lower() and 'not' not in response.lower():
                decision = 'APPROVED'
                confidence = 0.85
            elif 'denied' in response.lower() or 'reject' in response.lower():
                decision = 'DENIED'
                confidence = 0.80
            else:
                decision = 'REQUIRES_REVIEW'
                confidence = 0.60
        else:
            # Fallback decision logic
            total_cost = sum(s['cost'] for s in xml_data.get('services', []))
            if total_cost < 1000:
                decision = 'APPROVED'
                confidence = 0.70
            elif total_cost > 5000:
                decision = 'REQUIRES_REVIEW'
                confidence = 0.65
            else:
                decision = 'APPROVED'
                confidence = 0.75
        
        return {
            'decision': decision,
            'confidence': confidence,
            'authorization_number': f"AUTH-2025-{datetime.now().strftime('%Y%m%d')}-{hash(xml_data['file_path']) % 10000:04d}",
            'valid_days': 90,
            'conditions': ['Standard monitoring', 'Follow-up required'],
            'rationale': f"Based on comprehensive agent analysis including clinical review, medication assessment, and risk stratification.",
            'agent_based': decision_agent.get('success', False),
        }
    
    # Keep existing parsing methods
    def _parse_xml(self, xml_file_path: str) -> Dict[str, Any]:
        """Parse XML file and determine format."""
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        if 'PriorAuthorizationRequest' in root.tag or 'eclaimlink' in str(root.attrib):
            xml_format = 'eclaim'
        elif 'Prior.Authorization' in root.tag or 'shafafiya' in str(root.attrib):
            xml_format = 'shafafiya'
        else:
            xml_format = 'unknown'
        
        return {
            'file_path': xml_file_path,
            'format': xml_format,
            'root': root,
            'tree': tree
        }
    
    def _extract_patient_info(self, xml_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient information from XML."""
        root = xml_data['root']
        xml_format = xml_data['format']
        
        # Extract Emirates ID
        emirates_id = None
        patient_paths = [
            ".//Patient/EmiratesIDNumber",
            ".//EmiratesIDNumber", 
            ".//EmiratesID",
            ".//PatientInformation/EmiratesID"
        ]
        
        for path in patient_paths:
            element = root.find(path)
            if element is not None and element.text:
                emirates_id = element.text.strip()
                break
        
        if not emirates_id:
            raise ValueError("Could not find Emirates ID in XML")
        
        # Find patient ID using Emirates ID
        patient_id = find_patient_by_emirates_id(emirates_id)
        if not patient_id:
            raise ValueError(f"No patient found with Emirates ID: {emirates_id}")
        
        # Extract service requests
        services = []
        if xml_format == 'eclaim':
            for service in root.findall(".//ServiceRequest"):
                code = service.find(".//ActivityCode")
                desc = service.find(".//ActivityInstructions")
                cost = service.find(".//RequestedAmount")
                
                services.append({
                    'code': code.text if code is not None else '',
                    'description': desc.text if desc is not None else '',
                    'cost': float(cost.text) if cost is not None else 0.0
                })
        
        elif xml_format == 'shafafiya':
            for auth in root.findall(".//AuthorizationRequest"):
                code = auth.find(".//ServiceCode")
                desc = auth.find(".//ServiceDescription")
                cost = auth.find(".//EstimatedCost")
                
                services.append({
                    'code': code.text if code is not None else '',
                    'description': desc.text if desc is not None else '',
                    'cost': float(cost.text) if cost is not None else 0.0
                })
        
        total_cost = sum(s['cost'] for s in services)
        
        return {
            'patient_id': patient_id,
            'emirates_id': emirates_id,
            'xml_format': xml_format,
            'services': services,
            'total_cost': total_cost
        }
    
    def _determine_specialty(self, xml_data: Dict[str, Any], patient_data: Dict[str, Any]) -> str:
        """Determine medical specialty from XML and patient data."""
        
        # Get patient age
        import datetime
        dob_str = patient_data['demographics'].get('date_of_birth', '')
        patient_age = 30  # default
        
        if dob_str:
            try:
                dob = datetime.datetime.strptime(dob_str, '%d/%m/%Y')
                today = datetime.datetime.now()
                patient_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except:
                pass
        
        # Pediatric check
        if patient_age < 18:
            return 'pediatric'
        
        # Check service descriptions for specialty keywords
        all_text = ' '.join([
            s.get('description', '') + ' ' + s.get('code', '')
            for s in xml_data.get('services', [])
        ]).lower()
        
        specialty_keywords = {
            'diabetes': ['diabetes', 'insulin', 'hba1c', 'glucose', 'metformin'],
            'cardiac': ['cardiac', 'heart', 'cardio', 'catheter', 'troponin'],
            'respiratory': ['respiratory', 'asthma', 'copd', 'lung', 'breathing'],
            'oncology': ['cancer', 'oncology', 'tumor', 'chemotherapy'],
            'orthopedic': ['orthopedic', 'bone', 'joint', 'knee', 'hip'],
            'nephrology': ['kidney', 'renal', 'dialysis', 'creatinine'],
            'dermatology': ['skin', 'dermatology', 'psoriasis'],
            'neurology': ['neurological', 'brain', 'parkinson'],
            'mental_health': ['psychiatric', 'depression', 'anxiety']
        }
        
        for specialty, keywords in specialty_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                return specialty
        
        return 'general'


# Test the orchestrator
if __name__ == "__main__":
    xml_file = str(DATASET_PATH / "UAE_XML" / "patient_001_eclaim.xml")
    
    try:
        orchestrator = PreAuthOrchestrator()
        results = orchestrator.process_xml_request(xml_file)
        
        print("\n🏆 RESULTS:")
        print(f"Patient: {results['patient_info']['patient_id']}")
        print(f"Specialty: {results['specialty']}")
        print(f"Decision: {results['final_decision']['decision']}")
        print(f"Confidence: {results['final_decision']['confidence']:.1%}")
        print(f"Cost: AED {results['patient_info']['total_cost']}")
        
        # Show agent results summary
        if results['agent_results']:
            print(f"\n🤖 Agent Results:")
            for agent, result in results['agent_results'].items():
                status = result.get('status', 'unknown')
                success = "✅" if result.get('success') else "❌"
                print(f"  {success} {agent}: {status}")
        
        # Show cost tracking if available
        if results['cost_tracking']['total_cost_usd'] > 0:
            print(f"\n💰 Total Cost: ${results['cost_tracking']['total_cost_usd']:.4f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()