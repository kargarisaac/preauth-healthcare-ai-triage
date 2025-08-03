#!/usr/bin/env python3
"""
Claude Code Pre-Authorization Orchestrator
Medical pre-authorization analysis using specialized Claude Code agents

This orchestrator coordinates multiple specialized medical agents to provide
comprehensive pre-authorization analysis for UAE healthcare insurance.

Usage:
    python claude_preauth_orchestrator.py <current_request.xml> <patient_folder>

Agents Coordinated:
    1. clinical-analyzer: Medical history and disease progression analysis
    2. medication-specialist: Drug interactions and safety assessment  
    3. risk-assessor: Clinical risk stratification and outcome prediction
    4. decision-maker: Evidence-based authorization recommendations
    5. compliance-auditor: UAE regulatory compliance verification
"""

import asyncio
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import sys
import traceback
from loguru import logger

# Claude Code SDK imports
try:
    from claude_code_sdk import query, ClaudeCodeOptions, AssistantMessage, TextBlock, ResultMessage
    SDK_AVAILABLE = True
except ImportError:
    print("Warning: Claude Code SDK not available. Install with: pip install claude-code-sdk")
    SDK_AVAILABLE = False

# Configure loguru logging
logger.remove()  # Remove default handler
logger.add(
    "logs/preauth_orchestrator.log",
    rotation="10 MB",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO"
)
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
    level="INFO"
)

class PreAuthOrchestrator:
    """
    Main orchestrator class for coordinating Claude Code agents
    in medical pre-authorization analysis workflow
    """
    
    def __init__(self, current_request_path: str, patient_folder_path: str):
        self.current_request_path = Path(current_request_path)
        self.patient_folder_path = Path(patient_folder_path)
        self.output_dir = Path(f"analysis_results/analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Analysis results storage
        self.agent_results = {}
        self.token_usage = {}
        self.total_cost = 0.0
        self.analysis_metadata = {
            'start_time': datetime.now().isoformat(),
            'current_request': str(self.current_request_path),
            'patient_folder': str(self.patient_folder_path),
            'output_directory': str(self.output_dir)
        }
        
        # Agent configuration
        self.agents = {
            'clinical-analyzer': {
                'phase': 1,
                'dependencies': [],
                'description': 'Medical history and disease progression analysis'
            },
            'medication-specialist': {
                'phase': 1, 
                'dependencies': [],
                'description': 'Drug interactions and safety assessment'
            },
            'risk-assessor': {
                'phase': 2,
                'dependencies': ['clinical-analyzer', 'medication-specialist'],
                'description': 'Clinical risk stratification and outcome prediction'
            },
            'decision-maker': {
                'phase': 3,
                'dependencies': ['clinical-analyzer', 'medication-specialist', 'risk-assessor'],
                'description': 'Evidence-based authorization recommendations'
            },
            'compliance-auditor': {
                'phase': 3,
                'dependencies': ['decision-maker'],
                'description': 'UAE regulatory compliance verification'
            }
        }
        
        logger.info(f"Initialized PreAuth Orchestrator for {current_request_path}")
    
    async def validate_inputs(self) -> bool:
        """Validate input files and patient data"""
        try:
            # Validate current request file
            if not self.current_request_path.exists():
                logger.error(f"Current request file not found: {self.current_request_path}")
                return False
            
            # Validate XML structure
            try:
                tree = ET.parse(self.current_request_path)
                root = tree.getroot()
                logger.info(f"XML validated: {root.tag}")
            except ET.ParseError as e:
                logger.error(f"Invalid XML structure: {e}")
                return False
            
            # Validate patient folder
            if not self.patient_folder_path.exists():
                logger.error(f"Patient folder not found: {self.patient_folder_path}")
                return False
            
            # Check for required patient files
            required_files = ['profile.json', 'dataset_index.csv']
            for file_name in required_files:
                file_path = self.patient_folder_path / file_name
                if not file_path.exists():
                    logger.error(f"Required file not found: {file_name}")
                    return False
            
            logger.info("Input validation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            return False
    
    def prepare_agent_context(self, agent_name: str) -> str:
        """Prepare context data for specific agent"""
        context_data = {
            'current_request_file': str(self.current_request_path),
            'patient_folder': str(self.patient_folder_path),
            'agent_name': agent_name,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add previous agent results if available
        dependencies = self.agents[agent_name]['dependencies']
        if dependencies:
            context_data['previous_analyses'] = {dep: self.agent_results.get(dep, {}) 
                                               for dep in dependencies}
        
        return json.dumps(context_data, indent=2)
    
    def build_agent_prompt(self, agent_name: str) -> str:
        """Build comprehensive prompt for specific agent"""
        context = self.prepare_agent_context(agent_name)
        agent_description = self.agents[agent_name]['description']
        
        prompt = f"""You are a specialized {agent_name.replace('-', ' ')} agent conducting medical pre-authorization analysis.

**TASK**: Analyze the pre-authorization request and provide a comprehensive medical report.

**PATIENT DATA LOCATION**: {self.patient_folder_path}
**CURRENT REQUEST FILE**: {self.current_request_path}

**INSTRUCTIONS**:
1. Read the current XML request file
2. Read the patient profile.json file  
3. Read the dataset_index.csv for historical context
4. Read relevant historical XML files
5. Conduct your specialized analysis based on your expertise: {agent_description}

**REQUIRED OUTPUT FORMAT**:
# {agent_name.title().replace('-', ' ')} Analysis Report

## Executive Summary
- Key findings
- Primary recommendation (APPROVE/DENY/MORE INFO NEEDED)
- Confidence level (1-10)

## Detailed Analysis
[Your specialized analysis here]

## Evidence Base
[Clinical guidelines and literature references]

## UAE Healthcare Considerations
[Cultural, regulatory, and local factors]

## Recommendations
[Specific actionable recommendations]

**START ANALYSIS NOW** - Read the files and provide your comprehensive medical analysis."""
        return prompt
    
    def clean_agent_response(self, raw_response: str) -> str:
        """Clean raw agent response to extract meaningful medical analysis"""
        # Split by common delimiters and look for actual medical content
        lines = raw_response.split('\n')
        cleaned_lines = []
        in_medical_content = False
        
        for line in lines:
            # Skip system messages and metadata
            if any(skip_pattern in line for skip_pattern in [
                'SystemMessage', 'AssistantMessage', 'UserMessage', 'ToolResultBlock',
                'tool_use_id', 'session_id', 'ToolUseBlock', 'ResultMessage',
                'duration_ms', 'total_cost_usd', 'cache_creation_input_tokens'
            ]):
                continue
            
            # Look for medical report headers
            if any(header in line for header in [
                '# Clinical', '# Medication', '# Risk', '# Decision', '# Compliance',
                '## Executive Summary', '## Detailed Analysis', '## Evidence Base',
                '## UAE Healthcare', '## Recommendations'
            ]):
                in_medical_content = True
                cleaned_lines.append(line)
                continue
            
            # Include content if we're in a medical section
            if in_medical_content and line.strip():
                cleaned_lines.append(line)
        
        # If no structured content found, look for the last substantial text block
        if not cleaned_lines:
            # Find the longest text block that looks like medical analysis
            text_blocks = []
            current_block = []
            
            for line in lines:
                if line.strip() and not any(skip in line for skip in [
                    'SystemMessage', 'tool_use_id', 'session_id', 'duration_ms'
                ]):
                    current_block.append(line)
                elif current_block:
                    text_blocks.append('\n'.join(current_block))
                    current_block = []
            
            if current_block:
                text_blocks.append('\n'.join(current_block))
            
            # Return the longest block that contains medical keywords
            medical_keywords = ['patient', 'medical', 'diagnosis', 'treatment', 'recommendation', 'analysis']
            for block in sorted(text_blocks, key=len, reverse=True):
                if any(keyword.lower() in block.lower() for keyword in medical_keywords):
                    return block
            
            # Fallback: return the longest block
            if text_blocks:
                return max(text_blocks, key=len)
        
        return '\n'.join(cleaned_lines) if cleaned_lines else "Analysis completed but detailed report not properly formatted."
    
    async def run_agent(self, agent_name: str) -> Dict[str, Any]:
        """Execute specific Claude Code agent and return results"""
        if not SDK_AVAILABLE:
            logger.error("Claude Code SDK not available")
            return {"error": "SDK not available"}
        
        try:
            logger.info(f"Starting {agent_name} analysis...")
            
            # Build agent-specific prompt
            prompt = self.build_agent_prompt(agent_name)
            
            # Configure Claude Code options
            options = ClaudeCodeOptions(
                cwd=str(Path.cwd()),
                max_turns=20,  # Allow sufficient turns for comprehensive analysis
                allowed_tools=["Read", "Grep", "Glob"]
            )
            
            # Track token usage start
            start_time = datetime.now()
            agent_result = {
                'agent_name': agent_name,
                'start_time': start_time.isoformat(),
                'status': 'running'
            }
            
            # Execute Claude Code agent and extract meaningful responses
            text_responses = []
            all_messages = []
            usage_data = {}
            
            async for message in query(prompt=prompt, options=options):
                all_messages.append(str(message))
                
                # Extract meaningful text from AssistantMessage with TextBlock
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            text_responses.append(block.text)
                
                # Capture usage/cost data from ResultMessage only
                if isinstance(message, ResultMessage):
                    if hasattr(message, 'usage') and message.usage:
                        usage_data = {
                            'input_tokens': message.usage.get('input_tokens', 0),
                            'output_tokens': message.usage.get('output_tokens', 0),
                            'cache_creation_input_tokens': message.usage.get('cache_creation_input_tokens', 0),
                            'cache_read_input_tokens': message.usage.get('cache_read_input_tokens', 0),
                            'total_tokens': message.usage.get('input_tokens', 0) + message.usage.get('output_tokens', 0),
                            'service_tier': message.usage.get('service_tier', 'unknown')
                        }
                    
                    if hasattr(message, 'total_cost_usd') and message.total_cost_usd:
                        usage_data['total_cost_usd'] = float(message.total_cost_usd)
                    
                    # Also capture additional ResultMessage data
                    usage_data.update({
                        'duration_ms': getattr(message, 'duration_ms', 0),
                        'duration_api_ms': getattr(message, 'duration_api_ms', 0),
                        'num_turns': getattr(message, 'num_turns', 0),
                        'session_id': getattr(message, 'session_id', ''),
                        'is_error': getattr(message, 'is_error', False)
                    })
            
            # Combine meaningful text responses
            meaningful_response = "\n\n".join(text_responses) if text_responses else ""
            
            # Fallback to cleaning if no proper text blocks found
            if not meaningful_response.strip():
                full_response = "\n".join(all_messages)
                meaningful_response = self.clean_agent_response(full_response)
            
            # Record completion
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Store usage data for cost tracking
            if usage_data:
                self.token_usage[agent_name] = usage_data
                if 'total_cost_usd' in usage_data:
                    self.total_cost += usage_data['total_cost_usd']
            
            agent_result.update({
                'status': 'completed',
                'end_time': end_time.isoformat(),
                'processing_time_seconds': processing_time,
                'response': meaningful_response,  # Use meaningful response
                'raw_messages': all_messages,  # Keep raw for debugging
                'usage': usage_data,  # Include usage metrics
                'success': True
            })
            
            # Save individual agent result
            result_file = self.output_dir / f"{agent_name}_analysis.md"
            with open(result_file, 'w') as f:
                f.write(f"# {agent_name.title().replace('-', ' ')} Analysis Report\n\n")
                f.write(f"**Generated**: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Processing Time**: {processing_time:.2f} seconds\n")
                
                # Add usage metrics if available
                if usage_data:
                    f.write(f"**Token Usage**: {usage_data.get('total_tokens', 'N/A')} tokens\n")
                    f.write(f"  - Input tokens: {usage_data.get('input_tokens', 0)}\n")
                    f.write(f"  - Cache creation tokens: {usage_data.get('cache_creation_input_tokens', 0)}\n")
                    f.write(f"  - Cache read tokens: {usage_data.get('cache_read_input_tokens', 0)}\n")
                    f.write(f"  - Output tokens: {usage_data.get('output_tokens', 0)}\n")
                    f.write(f"**Cost**: ${usage_data.get('total_cost_usd', 0):.4f} USD\n")
                    f.write(f"**API Duration**: {usage_data.get('duration_api_ms', 0)} ms\n")
                    f.write(f"**Turns**: {usage_data.get('num_turns', 0)}\n")
                
                f.write("\n")
                f.write(meaningful_response)  # Use meaningful response
            
            # Save detailed logs for debugging
            log_file = self.output_dir / f"{agent_name}_debug.log"
            with open(log_file, 'w') as f:
                f.write(f"# Debug Log for {agent_name}\n\n")
                f.write(f"Generated: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Processing Time: {processing_time:.2f} seconds\n\n")
                f.write("## All Raw Messages:\n\n")
                for i, msg in enumerate(all_messages):
                    f.write(f"### Message {i+1}:\n{msg}\n\n")
            
            # Log completion with usage metrics
            cost_info = f" (${usage_data.get('total_cost_usd', 0):.4f})" if usage_data.get('total_cost_usd') else ""
            token_info = f" - {usage_data.get('total_tokens', 'N/A')} tokens" if usage_data.get('total_tokens') else ""
            logger.info(f"✅ {agent_name} completed successfully in {processing_time:.2f}s{cost_info}{token_info}")
            return agent_result
            
        except Exception as e:
            logger.error(f"❌ {agent_name} failed: {e}")
            error_result = {
                'agent_name': agent_name,
                'status': 'failed',
                'error': str(e),
                'traceback': traceback.format_exc(),
                'success': False
            }
            return error_result
    
    async def run_phase(self, phase_number: int) -> Dict[str, Any]:
        """Execute all agents in a specific phase"""
        phase_agents = [name for name, config in self.agents.items() 
                       if config['phase'] == phase_number]
        
        if not phase_agents:
            return {}
        
        logger.info(f"🚀 Starting Phase {phase_number} with agents: {', '.join(phase_agents)}")
        
        # Run agents in parallel within the same phase
        if len(phase_agents) > 1:
            tasks = [self.run_agent(agent_name) for agent_name in phase_agents]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = [await self.run_agent(phase_agents[0])]
        
        # Process results
        phase_results = {}
        for i, result in enumerate(results):
            agent_name = phase_agents[i]
            if isinstance(result, Exception):
                logger.error(f"Exception in {agent_name}: {result}")
                phase_results[agent_name] = {
                    'status': 'failed', 
                    'error': str(result),
                    'success': False
                }
            else:
                phase_results[agent_name] = result
                self.agent_results[agent_name] = result
        
        logger.info(f"✅ Phase {phase_number} completed")
        return phase_results
    
    async def orchestrate_analysis(self) -> Dict[str, Any]:
        """Main orchestration method coordinating all agents"""
        try:
            logger.info("🎯 Starting comprehensive pre-authorization analysis")
            
            # Validate inputs first
            if not await self.validate_inputs():
                raise ValueError("Input validation failed")
            
            # Execute agents in phases
            phase_results = {}
            
            # Phase 1: Parallel initial analysis
            logger.info("📋 Phase 1: Clinical and Medication Analysis")
            phase_results[1] = await self.run_phase(1)
            
            # Phase 2: Risk assessment (depends on Phase 1)
            logger.info("⚖️ Phase 2: Risk Stratification")
            phase_results[2] = await self.run_phase(2)
            
            # Phase 3: Decision and compliance (depends on previous phases)
            logger.info("🏥 Phase 3: Decision Making and Compliance")
            phase_results[3] = await self.run_phase(3)
            
            # Generate final analysis
            final_result = await self.generate_final_report()
            
            # Calculate total processing time
            total_processing_time = (datetime.now() - datetime.fromisoformat(self.analysis_metadata['start_time'])).total_seconds()
            
            # Update metadata with cost and usage information
            self.analysis_metadata.update({
                'end_time': datetime.now().isoformat(),
                'total_processing_time_seconds': total_processing_time,
                'total_agents': len(self.agents),
                'successful_agents': len([r for r in self.agent_results.values() if r.get('success')]),
                'failed_agents': len([r for r in self.agent_results.values() if not r.get('success')]),
                'phase_results': phase_results,
                'cost_tracking': {
                    'total_cost_usd': self.total_cost,
                    'token_usage_by_agent': self.token_usage,
                    'total_tokens': sum(usage.get('total_tokens', 0) for usage in self.token_usage.values())
                }
            })
            
            logger.info("🎉 Analysis orchestration completed successfully")
            return final_result
            
        except Exception as e:
            logger.error(f"💥 Orchestration failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'traceback': traceback.format_exc(),
                'partial_results': self.agent_results
            }
    
    async def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final report combining all agent analyses"""
        try:
            logger.info("📊 Generating comprehensive final report")
            
            # Calculate total processing time
            start_time = datetime.fromisoformat(self.analysis_metadata['start_time'])
            total_processing_time = (datetime.now() - start_time).total_seconds()
            
            # Collect all successful analyses
            successful_analyses = {name: result for name, result in self.agent_results.items() 
                                 if result.get('success', False)}
            
            if not successful_analyses:
                raise ValueError("No successful agent analyses available for final report")
            
            # Extract key findings from each agent
            clinical_findings = successful_analyses.get('clinical-analyzer', {}).get('response', 'Not available')
            medication_findings = successful_analyses.get('medication-specialist', {}).get('response', 'Not available')
            risk_findings = successful_analyses.get('risk-assessor', {}).get('response', 'Not available')
            decision_findings = successful_analyses.get('decision-maker', {}).get('response', 'Not available')
            compliance_findings = successful_analyses.get('compliance-auditor', {}).get('response', 'Not available')
            
            # Generate comprehensive final report
            final_report_content = f"""# Comprehensive Pre-Authorization Analysis Report

**Analysis ID**: {self.analysis_metadata.get('start_time', 'Unknown')}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Request File**: {self.current_request_path.name}
**Patient Folder**: {self.patient_folder_path.name}

## Executive Summary

This comprehensive pre-authorization analysis was conducted using specialized Claude Code agents to evaluate medical necessity, safety, and compliance for the submitted healthcare request.

### Analysis Components Completed
- ✅ **Clinical Analysis**: Medical history and disease progression assessment
- ✅ **Medication Assessment**: Drug interactions and safety evaluation  
- ✅ **Risk Stratification**: Clinical risk assessment and outcome prediction
- ✅ **Decision Support**: Evidence-based authorization recommendation
- ✅ **Compliance Audit**: UAE regulatory compliance verification

### Processing Summary
- **Total Processing Time**: {total_processing_time:.2f} seconds
- **Successful Agents**: {len(successful_analyses)}/{len(self.agents)}
- **Analysis Quality**: {'Excellent' if len(successful_analyses) == len(self.agents) else 'Partial'}
- **Total Cost**: ${self.total_cost:.4f} USD
- **Total Tokens**: {sum(usage.get('total_tokens', 0) for usage in self.token_usage.values())} tokens

---

## Clinical Analysis Summary

{clinical_findings}

---

## Medication Safety Assessment

{medication_findings}

---

## Risk Stratification Analysis

{risk_findings}

---

## Clinical Decision Recommendation

{decision_findings}

---

## Regulatory Compliance Verification

{compliance_findings}

---

## Technical Analysis Metadata

### Agent Execution Summary
"""
            
            # Add agent execution details with cost/token info
            for agent_name, result in successful_analyses.items():
                processing_time = result.get('processing_time_seconds', 0)
                status = result.get('status', 'unknown')
                usage = result.get('usage', {})
                cost = usage.get('total_cost_usd', 0)
                tokens = usage.get('total_tokens', 0)
                final_report_content += f"""
- **{agent_name}**: {status} ({processing_time:.2f}s, ${cost:.4f}, {tokens} tokens)"""
            
            # Add any failed agents
            failed_analyses = {name: result for name, result in self.agent_results.items() 
                             if not result.get('success', False)}
            if failed_analyses:
                final_report_content += "\n\n### Failed Analyses\n"
                for agent_name, result in failed_analyses.items():
                    error = result.get('error', 'Unknown error')
                    final_report_content += f"- **{agent_name}**: FAILED - {error}\n"
            
            final_report_content += f"""

### System Information
- **Analysis Start**: {self.analysis_metadata['start_time']}
- **Analysis End**: {datetime.now().isoformat()}
- **Output Directory**: {self.output_dir}
- **Claude Code SDK**: {'Available' if SDK_AVAILABLE else 'Not Available'}

---

*This report was generated by the Nazmito AI Pre-Authorization Analysis System using Claude Code specialized medical agents.*
"""
            
            # Save final report
            final_report_path = self.output_dir / "comprehensive_final_report.md"
            with open(final_report_path, 'w') as f:
                f.write(final_report_content)
            
            # Save metadata
            metadata_path = self.output_dir / "analysis_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(self.analysis_metadata, f, indent=2)
            
            logger.info(f"📄 Final report saved to: {final_report_path}")
            
            return {
                'status': 'completed',
                'final_report_path': str(final_report_path),
                'metadata_path': str(metadata_path),
                'successful_agents': len(successful_analyses),
                'total_agents': len(self.agents),
                'agent_results': self.agent_results,
                'analysis_metadata': self.analysis_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to generate final report: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'partial_results': self.agent_results
            }

async def main():
    """Main entry point for the orchestrator"""
    if len(sys.argv) != 3:
        print("Usage: python claude_preauth_orchestrator.py <current_request.xml> <patient_folder>")
        print("\nExample:")
        print("  python claude_preauth_orchestrator.py data/current_request.xml data/patient_123/")
        sys.exit(1)
    
    current_request = sys.argv[1]
    patient_folder = sys.argv[2]
    
    print("🏥 Nazmito AI Pre-Authorization Analysis System")
    print("=" * 60)
    print(f"📄 Current Request: {current_request}")
    print(f"📁 Patient Folder: {patient_folder}")
    print("=" * 60)
    
    if not SDK_AVAILABLE:
        print("❌ Claude Code SDK not available. Please install with:")
        print("   pip install claude-code-sdk")
        sys.exit(1)
    
    try:
        # Initialize orchestrator
        orchestrator = PreAuthOrchestrator(current_request, patient_folder)
        
        # Run comprehensive analysis
        result = await orchestrator.orchestrate_analysis()
        
        if result.get('status') == 'completed':
            print("\n🎉 Analysis completed successfully!")
            print(f"📊 Final Report: {result['final_report_path']}")
            print(f"🔍 Metadata: {result['metadata_path']}")
            print(f"✅ Successful Agents: {result['successful_agents']}/{result['total_agents']}")
            
            # Display cost and token usage
            total_cost = orchestrator.total_cost
            total_tokens = sum(usage.get('total_tokens', 0) for usage in orchestrator.token_usage.values())
            if total_cost > 0:
                print(f"💰 Total Cost: ${total_cost:.4f} USD")
            if total_tokens > 0:
                print(f"🔢 Total Tokens: {total_tokens:,}")
        else:
            print(f"\n❌ Analysis failed: {result.get('error', 'Unknown error')}")
            if result.get('partial_results'):
                print("📋 Partial results available in output directory")
        
    except KeyboardInterrupt:
        print("\n🛑 Analysis interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logger.error(f"Main execution failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Ensure output directories exist
    Path("logs").mkdir(exist_ok=True)
    Path("analysis_results").mkdir(exist_ok=True)
    
    # Run the async orchestrator
    asyncio.run(main())