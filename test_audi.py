# test_tester_debug.py
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.llm_config import LLMConfig
from src.agents.tester_agent import TesterAgent

def setup_test_environment():
    """Setup a clean test environment."""
    sandbox_root = "./sandbox_test_debug"
    
    # Clean up if exists
    if os.path.exists(sandbox_root):
        import shutil
        shutil.rmtree(sandbox_root)
    
    # Create fresh sandbox
    os.makedirs(sandbox_root, exist_ok=True)
    
    # Create a sample Python file to test
    sample_file = os.path.join(sandbox_root, "sample.py")
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write("""
def add(a, b):
    '''Add two numbers.'''
    return a + b

def subtract(a, b):
    '''Subtract b from a.'''
    return a - b

def multiply(a, b):
    '''Multiply two numbers.'''
    return a * b

def divide(a, b):
    '''Divide a by b.'''
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
""")
    
    print(f"📁 Created sandbox at: {sandbox_root}")
    print(f"📄 Created sample.py with 4 functions")
    
    return sandbox_root

def main():
    """Main test function."""
    print("=" * 60)
    print("🧪 TESTER AGENT DEBUG TEST")
    print("=" * 60)
    
    # Setup environment
    sandbox_root = setup_test_environment()
    
    # List files
    print("\n📁 Files in sandbox:")
    for f in os.listdir(sandbox_root):
        print(f"  - {f}")
    
    # Initialize LLM
    print(f"\n🤖 Initializing LLM...")
    try:
        llm_config = LLMConfig(model_name="gemini-2.5-flash")
        print(f"   LLM initialized: {llm_config.get_model_name()}")
    except Exception as e:
        print(f"   ❌ LLM initialization failed: {e}")
        # Use mock LLM for testing
        class MockLLM:
            def generate(self, prompt, **kwargs):
                return '''```python
import pytest
from sample import add, subtract, multiply, divide

def test_add():
    """Test addition function."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_subtract():
    """Test subtraction function."""
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5
    assert subtract(10, 10) == 0

def test_multiply():
    """Test multiplication function."""
    assert multiply(3, 4) == 12
    assert multiply(-2, 3) == -6
    assert multiply(0, 100) == 0

def test_divide():
    """Test division function."""
    assert divide(10, 2) == 5
    assert divide(9, 3) == 3
    with pytest.raises(ValueError):
        divide(5, 0)
```'''
            
            def get_model_name(self):
                return "mock-gemini-2.5-flash"
        
        llm_config = MockLLM()
        print(f"   Using mock LLM for testing")
    
    # Initialize TesterAgent
    print(f"\n👨‍💻 Initializing TesterAgent...")
    tester = TesterAgent(sandbox_root=sandbox_root, llm=llm_config)
    
    # Run test
    print(f"\n⚡ Running test_file('sample.py')...")
    result = tester.test_file("sample.py")
    
    # Print results
    print(f"\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    import json
    print(json.dumps(result, indent=2, default=str))
    
    # Summary
    print(f"\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print(f"Success: {result.get('success', False)}")
    print(f"Retry needed: {result.get('retry_needed', False)}")
    
    if result.get('success'):
        print("✅ Test passed!")
    else:
        print("❌ Test failed")
        if 'error' in result:
            print(f"Error: {result['error']}")
    
    # Check for test file creation
    print(f"\n📁 Final files in sandbox:")
    for f in os.listdir(sandbox_root):
        print(f"  - {f}")

if __name__ == "__main__":
    main()