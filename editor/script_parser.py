
import ast
import os

class ScriptParser:
    """Extracts default property values from Python scripts."""
    
    @staticmethod
    def parse_properties(script_path):
        """
        Parses a python script and finds variable assignments in start() or __init__.
        Returns a dictionary of {var_name: default_value}.
        Only supports simple literals (int, float, str, bool).
        """
        props = {}
        
        if not os.path.exists(script_path):
            return props
            
        try:
            with open(script_path, "r") as f:
                tree = ast.parse(f.read(), filename=script_path)
                
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check methods inside the class
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name in ["__init__", "start"]:
                            ScriptParser._extract_assignments(item, props)
                            
        except Exception as e:
            print(f"Error parsing script {script_path}: {e}")
            
        return props

    @staticmethod
    def _extract_assignments(func_node, props):
        for stmt in func_node.body:
            # Look for self.var = value
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                        if target.value.id == "self":
                            var_name = target.attr
                            
                            # Filter out protected/private vars
                            if var_name.startswith("_"):
                                continue
                                
                            val = ScriptParser._get_literal_value(stmt.value)
                            if val is not None:
                                props[var_name] = val

    @staticmethod
    def _get_literal_value(node):
        if isinstance(node, ast.Constant): # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num): # Python < 3.8
            return node.n
        elif isinstance(node, ast.Str): # Python < 3.8
            return node.s
        elif isinstance(node, ast.NameConstant): # True/False/None
            return node.value
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            # Handle negative numbers: -5
            val = ScriptParser._get_literal_value(node.operand)
            if isinstance(val, (int, float)):
                return -val
        return None
