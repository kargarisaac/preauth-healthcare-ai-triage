#!/usr/bin/env python3
"""Quick test of the orchestrator system."""

import sys
from pathlib import Path

# Add data_ingestion to path for ETL access
sys.path.append(str(Path(__file__).parent.parent / "data_ingestion"))

from etl import DATASET_PATH
from orchestrator import PreAuthOrchestrator

def test_orchestrator_initialization():
    """Test orchestrator initialization and agent loading."""
    print("🧪 Testing Orchestrator Initialization")
    print("=" * 50)
    
    try:
        orchestrator = PreAuthOrchestrator()
        
        print(f"✅ Agents directory: {orchestrator.agents_dir}")
        print(f"✅ Number of agents configured: {len(orchestrator.agents)}")
        print(f"✅ Agent definitions loaded: {len(orchestrator.agent_definitions)}")
        
        print("\n📋 Configured Agents:")
        for agent_name, config in orchestrator.agents.items():
            definition = orchestrator.agent_definitions.get(agent_name, {})
            print(f"  • {agent_name}")
            print(f"    Phase: {config['phase']}")
            print(f"    Dependencies: {config['dependencies']}")
            print(f"    Definition loaded: {'✅' if definition else '❌'}")
            if definition:
                print(f"    Instructions: {len(definition.get('instructions', ''))} chars")
        
        print("\n🔧 Agent Phases:")
        phases = {}
        for agent_name, config in orchestrator.agents.items():
            phase = config['phase']
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(agent_name)
        
        for phase_num in sorted(phases.keys()):
            agents = phases[phase_num]
            print(f"  Phase {phase_num}: {', '.join(agents)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator initialization failed: {e}")
        return False

def test_xml_parsing():
    """Test XML parsing capabilities."""
    print("\n🧪 Testing XML Parsing")
    print("=" * 30)
    
    xml_file = str(DATASET_PATH / "UAE_XML" / "patient_001_eclaim.xml")
    
    try:
        orchestrator = PreAuthOrchestrator()
        
        # Test XML parsing
        xml_data = orchestrator._parse_xml(xml_file)
        print(f"✅ XML file parsed: {xml_data['format']}")
        
        # Test patient info extraction
        patient_info = orchestrator._extract_patient_info(xml_data)
        print(f"✅ Patient ID found: {patient_info['patient_id']}")
        print(f"✅ Emirates ID: {patient_info['emirates_id']}")
        print(f"✅ Services: {len(patient_info['services'])}")
        print(f"✅ Total cost: AED {patient_info['total_cost']}")
        
        return True
        
    except Exception as e:
        print(f"❌ XML parsing failed: {e}")
        return False

def test_agent_definitions():
    """Test agent definition files."""
    print("\n🧪 Testing Agent Definition Files")
    print("=" * 40)
    
    try:
        orchestrator = PreAuthOrchestrator()
        
        for agent_name in orchestrator.agents.keys():
            agent_file = orchestrator.agents_dir / f"{agent_name}.md"
            definition = orchestrator.agent_definitions.get(agent_name)
            
            if agent_file.exists():
                print(f"✅ {agent_name}: File exists")
                if definition and definition.get('instructions'):
                    instructions_len = len(definition['instructions'])
                    print(f"    Instructions: {instructions_len} characters")
                else:
                    print(f"    ⚠️  Instructions not loaded properly")
            else:
                print(f"📝 {agent_name}: Default file created")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent definition test failed: {e}")
        return False

if __name__ == "__main__":
    print("🏥 Nazmito Pre-Authorization Orchestrator Test Suite")
    print("=" * 60)
    
    tests = [
        test_orchestrator_initialization,
        test_xml_parsing,
        test_agent_definitions,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n🏆 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("✅ All tests passed! Orchestrator is ready for agent execution.")
        print("\n💡 To run with real Claude Code agents:")
        print("   python orchestrator.py")
        print("   (requires claude-code-sdk)")
    else:
        print("❌ Some tests failed. Please check the configuration.")