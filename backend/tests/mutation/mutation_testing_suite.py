# 🧪 MUTATION TESTING SUITE - Phase 4 Implementation
"""
Advanced mutation testing for test quality validation
Security-focused mutation testing and code coverage analysis

Phase 4: Mutation testing for EXCELLENT level test quality
"""

import ast
import asyncio
import subprocess
import tempfile
import shutil
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
import time
import random

logger = logging.getLogger(__name__)


class MutationType(str, Enum):
    """Types of mutations to apply"""
    ARITHMETIC = "arithmetic"          # +, -, *, /, %
    COMPARISON = "comparison"          # ==, !=, <, >, <=, >=
    LOGICAL = "logical"               # and, or, not
    ASSIGNMENT = "assignment"         # = to +=, -=, etc.
    CONDITIONAL = "conditional"       # if conditions
    LOOP = "loop"                    # for, while modifications
    RETURN = "return"                # return value changes
    EXCEPTION = "exception"          # exception handling
    SECURITY = "security"            # security-specific mutations


@dataclass
class MutationResult:
    """Result of a single mutation test"""
    mutation_id: str
    mutation_type: MutationType
    original_code: str
    mutated_code: str
    file_path: str
    line_number: int
    killed: bool  # True if tests caught the mutation
    execution_time: float
    test_output: str
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mutation_id": self.mutation_id,
            "mutation_type": self.mutation_type.value,
            "original_code": self.original_code,
            "mutated_code": self.mutated_code,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "killed": self.killed,
            "execution_time": self.execution_time,
            "test_output": self.test_output,
            "error": self.error
        }


@dataclass
class MutationTestReport:
    """Comprehensive mutation testing report"""
    total_mutations: int
    killed_mutations: int
    survived_mutations: int
    mutation_score: float
    execution_time: float
    mutations_by_type: Dict[str, Dict[str, int]]
    survived_mutations_details: List[MutationResult]
    security_mutations: List[MutationResult]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_mutations": self.total_mutations,
                "killed_mutations": self.killed_mutations,
                "survived_mutations": self.survived_mutations,
                "mutation_score": self.mutation_score,
                "execution_time": self.execution_time
            },
            "mutations_by_type": self.mutations_by_type,
            "survived_mutations": [m.to_dict() for m in self.survived_mutations_details],
            "security_mutations": [m.to_dict() for m in self.security_mutations],
            "recommendations": self.recommendations
        }


class CodeMutator(ast.NodeTransformer):
    """AST-based code mutator for generating test mutations"""
    
    def __init__(self, mutation_types: Set[MutationType] = None):
        self.mutation_types = mutation_types or set(MutationType)
        self.mutations: List[Dict[str, Any]] = []
        self.current_line = 0
    
    def visit(self, node):
        """Visit AST node and track line numbers"""
        if hasattr(node, 'lineno'):
            self.current_line = node.lineno
        return super().visit(node)
    
    def visit_BinOp(self, node):
        """Mutate binary operations (arithmetic, comparison)"""
        if MutationType.ARITHMETIC in self.mutation_types:
            if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)):
                original_op = type(node.op).__name__
                
                # Arithmetic mutations
                mutations = {
                    'Add': [ast.Sub(), ast.Mult()],
                    'Sub': [ast.Add(), ast.Div()],
                    'Mult': [ast.Add(), ast.Div()],
                    'Div': [ast.Mult(), ast.Sub()],
                    'Mod': [ast.Add(), ast.Mult()]
                }
                
                if original_op in mutations:
                    for new_op in mutations[original_op]:
                        mutated_node = ast.copy_location(
                            ast.BinOp(left=node.left, op=new_op, right=node.right),
                            node
                        )
                        self.mutations.append({
                            'type': MutationType.ARITHMETIC,
                            'line': self.current_line,
                            'original': ast.unparse(node),
                            'mutated': ast.unparse(mutated_node),
                            'node': mutated_node
                        })
        
        return self.generic_visit(node)
    
    def visit_Compare(self, node):
        """Mutate comparison operations"""
        if MutationType.COMPARISON in self.mutation_types:
            for i, op in enumerate(node.ops):
                original_op = type(op).__name__
                
                # Comparison mutations
                mutations = {
                    'Eq': [ast.NotEq(), ast.Lt(), ast.Gt()],
                    'NotEq': [ast.Eq(), ast.Lt(), ast.Gt()],
                    'Lt': [ast.Gt(), ast.LtE(), ast.Eq()],
                    'Gt': [ast.Lt(), ast.GtE(), ast.Eq()],
                    'LtE': [ast.GtE(), ast.Lt(), ast.NotEq()],
                    'GtE': [ast.LtE(), ast.Gt(), ast.NotEq()]
                }
                
                if original_op in mutations:
                    for new_op in mutations[original_op]:
                        new_ops = node.ops[:]
                        new_ops[i] = new_op
                        mutated_node = ast.copy_location(
                            ast.Compare(left=node.left, ops=new_ops, comparators=node.comparators),
                            node
                        )
                        self.mutations.append({
                            'type': MutationType.COMPARISON,
                            'line': self.current_line,
                            'original': ast.unparse(node),
                            'mutated': ast.unparse(mutated_node),
                            'node': mutated_node
                        })
        
        return self.generic_visit(node)
    
    def visit_BoolOp(self, node):
        """Mutate boolean operations"""
        if MutationType.LOGICAL in self.mutation_types:
            if isinstance(node.op, ast.And):
                mutated_node = ast.copy_location(
                    ast.BoolOp(op=ast.Or(), values=node.values),
                    node
                )
            elif isinstance(node.op, ast.Or):
                mutated_node = ast.copy_location(
                    ast.BoolOp(op=ast.And(), values=node.values),
                    node
                )
            else:
                return self.generic_visit(node)
            
            self.mutations.append({
                'type': MutationType.LOGICAL,
                'line': self.current_line,
                'original': ast.unparse(node),
                'mutated': ast.unparse(mutated_node),
                'node': mutated_node
            })
        
        return self.generic_visit(node)
    
    def visit_UnaryOp(self, node):
        """Mutate unary operations"""
        if MutationType.LOGICAL in self.mutation_types:
            if isinstance(node.op, ast.Not):
                # Remove 'not' operator
                mutated_node = node.operand
                self.mutations.append({
                    'type': MutationType.LOGICAL,
                    'line': self.current_line,
                    'original': ast.unparse(node),
                    'mutated': ast.unparse(mutated_node),
                    'node': mutated_node
                })
        
        return self.generic_visit(node)
    
    def visit_If(self, node):
        """Mutate conditional statements"""
        if MutationType.CONDITIONAL in self.mutation_types:
            # Negate condition
            if isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not):
                # Remove double negation
                mutated_test = node.test.operand
            else:
                # Add negation
                mutated_test = ast.UnaryOp(op=ast.Not(), operand=node.test)
            
            mutated_node = ast.copy_location(
                ast.If(test=mutated_test, body=node.body, orelse=node.orelse),
                node
            )
            
            self.mutations.append({
                'type': MutationType.CONDITIONAL,
                'line': self.current_line,
                'original': f"if {ast.unparse(node.test)}:",
                'mutated': f"if {ast.unparse(mutated_test)}:",
                'node': mutated_node
            })
        
        return self.generic_visit(node)
    
    def visit_Return(self, node):
        """Mutate return statements"""
        if MutationType.RETURN in self.mutation_types and node.value:
            # Different return value mutations based on type
            mutations = []
            
            if isinstance(node.value, ast.Constant):
                if node.value.value is True:
                    mutations.append(ast.Constant(value=False))
                elif node.value.value is False:
                    mutations.append(ast.Constant(value=True))
                elif isinstance(node.value.value, (int, float)) and node.value.value != 0:
                    mutations.append(ast.Constant(value=0))
                elif node.value.value == 0:
                    mutations.append(ast.Constant(value=1))
                elif isinstance(node.value.value, str) and node.value.value:
                    mutations.append(ast.Constant(value=""))
                elif node.value.value == "":
                    mutations.append(ast.Constant(value="mutated"))
            
            for mutation in mutations:
                mutated_node = ast.copy_location(
                    ast.Return(value=mutation),
                    node
                )
                self.mutations.append({
                    'type': MutationType.RETURN,
                    'line': self.current_line,
                    'original': ast.unparse(node),
                    'mutated': ast.unparse(mutated_node),
                    'node': mutated_node
                })
        
        return self.generic_visit(node)
    
    def visit_Try(self, node):
        """Mutate exception handling (security-focused)"""
        if MutationType.SECURITY in self.mutation_types:
            # Remove exception handling (security risk)
            if node.handlers:
                mutated_node = ast.copy_location(
                    ast.Module(body=node.body, type_ignores=[]),
                    node
                )
                self.mutations.append({
                    'type': MutationType.SECURITY,
                    'line': self.current_line,
                    'original': "try: ... except: ...",
                    'mutated': "# Exception handling removed",
                    'node': mutated_node,
                    'security_risk': True
                })
        
        return self.generic_visit(node)


class SecurityMutator:
    """Specialized mutator for security-related mutations"""
    
    @staticmethod
    def generate_security_mutations(code: str) -> List[Dict[str, Any]]:
        """Generate security-focused mutations"""
        mutations = []
        
        # Authentication bypass mutations
        if "verify_password" in code or "check_password" in code:
            mutations.append({
                'type': MutationType.SECURITY,
                'description': 'Authentication bypass - always return True',
                'pattern': r'return\s+verify_password\([^)]+\)',
                'replacement': 'return True',
                'risk': 'CRITICAL'
            })
        
        # Authorization bypass mutations
        if "has_permission" in code or "check_permission" in code:
            mutations.append({
                'type': MutationType.SECURITY,
                'description': 'Authorization bypass - always allow access',
                'pattern': r'return\s+has_permission\([^)]+\)',
                'replacement': 'return True',
                'risk': 'CRITICAL'
            })
        
        # Token validation bypass
        if "validate_token" in code or "verify_token" in code:
            mutations.append({
                'type': MutationType.SECURITY,
                'description': 'Token validation bypass',
                'pattern': r'return\s+validate_token\([^)]+\)',
                'replacement': 'return True',
                'risk': 'CRITICAL'
            })
        
        # Input validation bypass
        if "validate_input" in code or "sanitize" in code:
            mutations.append({
                'type': MutationType.SECURITY,
                'description': 'Input validation bypass',
                'pattern': r'if\s+validate_input\([^)]+\):',
                'replacement': 'if True:',
                'risk': 'HIGH'
            })
        
        # Rate limiting bypass
        if "rate_limit" in code or "check_rate_limit" in code:
            mutations.append({
                'type': MutationType.SECURITY,
                'description': 'Rate limiting bypass',
                'pattern': r'if\s+check_rate_limit\([^)]+\):',
                'replacement': 'if True:',
                'risk': 'MEDIUM'
            })
        
        return mutations


class MutationTestRunner:
    """Run mutation tests and analyze results"""
    
    def __init__(self, 
                 source_dir: str = "backend/app",
                 test_dir: str = "backend/tests",
                 excluded_files: List[str] = None):
        
        self.source_dir = Path(source_dir)
        self.test_dir = Path(test_dir)
        self.excluded_files = excluded_files or [
            "__pycache__", ".pyc", "test_", "conftest.py"
        ]
        
        self.mutation_results: List[MutationResult] = []
        self.temp_dir: Optional[Path] = None
    
    async def run_mutation_testing(self, 
                                  files: Optional[List[str]] = None,
                                  mutation_types: Optional[Set[MutationType]] = None) -> MutationTestReport:
        """Run comprehensive mutation testing"""
        
        start_time = time.time()
        logger.info("🧪 Starting mutation testing suite...")
        
        # Setup temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="mutation_test_"))
        
        try:
            # Get files to test
            test_files = files or self._discover_source_files()
            
            # Generate mutations
            mutations = await self._generate_mutations(test_files, mutation_types)
            logger.info(f"Generated {len(mutations)} mutations")
            
            # Run mutations
            results = await self._run_mutations(mutations)
            
            # Generate report
            report = self._generate_report(results, time.time() - start_time)
            
            logger.info(f"✅ Mutation testing completed: {report.mutation_score:.1f}% score")
            return report
            
        finally:
            # Cleanup
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
    
    def _discover_source_files(self) -> List[str]:
        """Discover Python source files to test"""
        files = []
        
        for file_path in self.source_dir.rglob("*.py"):
            # Skip excluded files
            if any(excluded in str(file_path) for excluded in self.excluded_files):
                continue
            
            files.append(str(file_path))
        
        return files
    
    async def _generate_mutations(self, 
                                 files: List[str], 
                                 mutation_types: Optional[Set[MutationType]]) -> List[Dict[str, Any]]:
        """Generate mutations for source files"""
        
        all_mutations = []
        mutation_types = mutation_types or set(MutationType)
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                # Parse AST
                tree = ast.parse(source_code)
                
                # Generate standard mutations
                mutator = CodeMutator(mutation_types)
                mutator.visit(tree)
                
                for mutation in mutator.mutations:
                    mutation['file_path'] = file_path
                    mutation['source_code'] = source_code
                    all_mutations.append(mutation)
                
                # Generate security mutations
                if MutationType.SECURITY in mutation_types:
                    security_mutations = SecurityMutator.generate_security_mutations(source_code)
                    for mutation in security_mutations:
                        mutation['file_path'] = file_path
                        mutation['source_code'] = source_code
                        all_mutations.append(mutation)
                
            except Exception as e:
                logger.warning(f"Failed to generate mutations for {file_path}: {e}")
        
        return all_mutations
    
    async def _run_mutations(self, mutations: List[Dict[str, Any]]) -> List[MutationResult]:
        """Run mutations and collect results"""
        
        results = []
        total_mutations = len(mutations)
        
        for i, mutation in enumerate(mutations):
            logger.info(f"Running mutation {i+1}/{total_mutations}")
            
            try:
                result = await self._run_single_mutation(mutation)
                results.append(result)
                
                if result.killed:
                    logger.debug(f"✅ Mutation killed: {result.mutation_id}")
                else:
                    logger.warning(f"❌ Mutation survived: {result.mutation_id}")
                    
            except Exception as e:
                logger.error(f"Failed to run mutation {i+1}: {e}")
        
        return results
    
    async def _run_single_mutation(self, mutation: Dict[str, Any]) -> MutationResult:
        """Run a single mutation test"""
        
        mutation_id = f"{Path(mutation['file_path']).name}:{mutation['line']}:{mutation['type'].value}"
        start_time = time.time()
        
        # Create mutated file
        mutated_file = self._create_mutated_file(mutation)
        
        try:
            # Run tests
            test_output, return_code = await self._run_tests()
            
            # Determine if mutation was killed
            killed = return_code != 0  # Tests failed = mutation detected
            
            return MutationResult(
                mutation_id=mutation_id,
                mutation_type=MutationType(mutation['type']),
                original_code=mutation['original'],
                mutated_code=mutation['mutated'],
                file_path=mutation['file_path'],
                line_number=mutation['line'],
                killed=killed,
                execution_time=time.time() - start_time,
                test_output=test_output
            )
            
        except Exception as e:
            return MutationResult(
                mutation_id=mutation_id,
                mutation_type=MutationType(mutation['type']),
                original_code=mutation['original'],
                mutated_code=mutation['mutated'],
                file_path=mutation['file_path'],
                line_number=mutation['line'],
                killed=False,
                execution_time=time.time() - start_time,
                test_output="",
                error=str(e)
            )
        
        finally:
            # Restore original file
            self._restore_original_file(mutation)
    
    def _create_mutated_file(self, mutation: Dict[str, Any]) -> str:
        """Create mutated version of source file"""
        
        file_path = mutation['file_path']
        source_code = mutation['source_code']
        
        # Apply mutation (simplified - would need more sophisticated replacement)
        mutated_code = source_code.replace(
            mutation['original'], 
            mutation['mutated'], 
            1  # Replace only first occurrence
        )
        
        # Backup original
        backup_path = f"{file_path}.backup"
        shutil.copy2(file_path, backup_path)
        
        # Write mutated version
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(mutated_code)
        
        return backup_path
    
    def _restore_original_file(self, mutation: Dict[str, Any]):
        """Restore original file from backup"""
        
        file_path = mutation['file_path']
        backup_path = f"{file_path}.backup"
        
        if Path(backup_path).exists():
            shutil.move(backup_path, file_path)
    
    async def _run_tests(self) -> Tuple[str, int]:
        """Run test suite and return output and return code"""
        
        try:
            # Run pytest
            process = await asyncio.create_subprocess_exec(
                "python", "-m", "pytest", str(self.test_dir), "-v", "--tb=short",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.source_dir.parent
            )
            
            stdout, _ = await process.communicate()
            output = stdout.decode('utf-8')
            
            return output, process.returncode
            
        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
            return str(e), 1
    
    def _generate_report(self, results: List[MutationResult], execution_time: float) -> MutationTestReport:
        """Generate comprehensive mutation testing report"""
        
        total_mutations = len(results)
        killed_mutations = sum(1 for r in results if r.killed)
        survived_mutations = total_mutations - killed_mutations
        
        mutation_score = (killed_mutations / total_mutations * 100) if total_mutations > 0 else 0
        
        # Analyze by mutation type
        mutations_by_type = {}
        for result in results:
            mut_type = result.mutation_type.value
            if mut_type not in mutations_by_type:
                mutations_by_type[mut_type] = {"total": 0, "killed": 0, "survived": 0}
            
            mutations_by_type[mut_type]["total"] += 1
            if result.killed:
                mutations_by_type[mut_type]["killed"] += 1
            else:
                mutations_by_type[mut_type]["survived"] += 1
        
        # Get survived mutations details
        survived_mutations_details = [r for r in results if not r.killed]
        
        # Get security mutations
        security_mutations = [r for r in results if r.mutation_type == MutationType.SECURITY]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            mutation_score, survived_mutations_details, security_mutations
        )
        
        return MutationTestReport(
            total_mutations=total_mutations,
            killed_mutations=killed_mutations,
            survived_mutations=survived_mutations,
            mutation_score=mutation_score,
            execution_time=execution_time,
            mutations_by_type=mutations_by_type,
            survived_mutations_details=survived_mutations_details,
            security_mutations=security_mutations,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, 
                                mutation_score: float,
                                survived_mutations: List[MutationResult],
                                security_mutations: List[MutationResult]) -> List[str]:
        """Generate recommendations based on mutation testing results"""
        
        recommendations = []
        
        # Overall score recommendations
        if mutation_score < 60:
            recommendations.append("CRITICAL: Mutation score below 60%. Significant improvement in test quality needed.")
        elif mutation_score < 80:
            recommendations.append("WARNING: Mutation score below 80%. Consider adding more comprehensive tests.")
        elif mutation_score < 95:
            recommendations.append("GOOD: Mutation score above 80%. Consider targeting edge cases for improvement.")
        else:
            recommendations.append("EXCELLENT: High mutation score achieved. Maintain test quality.")
        
        # Security-specific recommendations
        security_survived = [m for m in security_mutations if not m.killed]
        if security_survived:
            recommendations.append(
                f"SECURITY ALERT: {len(security_survived)} security mutations survived. "
                "Review security test coverage immediately."
            )
        
        # Type-specific recommendations
        type_recommendations = {
            MutationType.COMPARISON: "Add edge case tests for boundary conditions",
            MutationType.LOGICAL: "Test both true and false paths in boolean logic",
            MutationType.CONDITIONAL: "Ensure all conditional branches are tested",
            MutationType.RETURN: "Verify return value handling in all scenarios",
            MutationType.ARITHMETIC: "Test arithmetic operations with edge values"
        }
        
        for mutation in survived_mutations[:5]:  # Top 5 issues
            if mutation.mutation_type in type_recommendations:
                rec = f"{mutation.file_path}:{mutation.line_number} - {type_recommendations[mutation.mutation_type]}"
                if rec not in recommendations:
                    recommendations.append(rec)
        
        return recommendations


# Convenience function for running mutation tests
async def run_mutation_testing_suite(
    source_dir: str = "backend/app",
    test_dir: str = "backend/tests",
    files: Optional[List[str]] = None,
    mutation_types: Optional[Set[MutationType]] = None
) -> MutationTestReport:
    """Run comprehensive mutation testing suite"""
    
    runner = MutationTestRunner(source_dir, test_dir)
    return await runner.run_mutation_testing(files, mutation_types)


# Example usage for security-focused testing
async def run_security_mutation_testing() -> MutationTestReport:
    """Run mutation testing focused on security"""
    
    security_types = {MutationType.SECURITY, MutationType.CONDITIONAL, MutationType.COMPARISON}
    
    return await run_mutation_testing_suite(
        source_dir="backend/app",
        test_dir="backend/tests",
        mutation_types=security_types
    )


if __name__ == "__main__":
    # Run mutation testing
    asyncio.run(run_mutation_testing_suite())
