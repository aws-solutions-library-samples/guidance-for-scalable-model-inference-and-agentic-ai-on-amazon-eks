from mcp.server import FastMCP
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Initialize MCP server for healthcare data
mcp = FastMCP("Healthcare Data Server", host="0.0.0.0")

# Sample healthcare data (in production, this would connect to a real database/API)
SAMPLE_PATIENTS = {
    "PAT001": {
        "patient_id": "PAT001",
        "name": "John Doe",
        "date_of_birth": "1975-03-15",
        "gender": "Male",
        "age": 49
    },
    "PAT002": {
        "patient_id": "PAT002", 
        "name": "Jane Smith",
        "date_of_birth": "1982-07-22",
        "gender": "Female",
        "age": 42
    },
    "PAT003": {
        "patient_id": "PAT003",
        "name": "Robert Johnson", 
        "date_of_birth": "1965-11-08",
        "gender": "Male",
        "age": 59
    }
}

SAMPLE_MEDICAL_HISTORY = {
    "PAT001": [
        {
            "condition": "Type 2 Diabetes Mellitus",
            "diagnosis_date": "2020-01-15",
            "status": "active",
            "severity": "moderate",
            "notes": "Well controlled with medication",
            "provider": "Dr. Smith"
        },
        {
            "condition": "Hypertension",
            "diagnosis_date": "2018-06-01", 
            "status": "active",
            "severity": "mild",
            "notes": "Controlled with ACE inhibitor",
            "provider": "Dr. Smith"
        }
    ],
    "PAT002": [
        {
            "condition": "Hypothyroidism",
            "diagnosis_date": "2019-03-10",
            "status": "active", 
            "severity": "mild",
            "notes": "On levothyroxine replacement",
            "provider": "Dr. Jones"
        }
    ],
    "PAT003": [
        {
            "condition": "Coronary Artery Disease",
            "diagnosis_date": "2021-09-15",
            "status": "active",
            "severity": "high", 
            "notes": "Post-MI, on dual antiplatelet therapy",
            "provider": "Dr. Brown"
        }
    ]
}

SAMPLE_LAB_RESULTS = {
    "PAT001": [
        {
            "test_name": "Glucose, Fasting",
            "value": "145",
            "unit": "mg/dL",
            "reference_range": "70-100",
            "status": "final",
            "abnormal_flag": "H",
            "collection_date": "2025-01-15",
            "result_date": "2025-01-15",
            "ordering_provider": "Dr. Smith",
            "notes": "Elevated - diabetes monitoring"
        },
        {
            "test_name": "Hemoglobin A1c",
            "value": "7.2",
            "unit": "%", 
            "reference_range": "<5.7",
            "status": "final",
            "abnormal_flag": "H",
            "collection_date": "2025-01-15",
            "result_date": "2025-01-15",
            "ordering_provider": "Dr. Smith",
            "notes": "Above target for diabetes"
        },
        {
            "test_name": "Total Cholesterol",
            "value": "185",
            "unit": "mg/dL",
            "reference_range": "<200",
            "status": "final",
            "abnormal_flag": "",
            "collection_date": "2025-01-15", 
            "result_date": "2025-01-15",
            "ordering_provider": "Dr. Smith",
            "notes": "Within normal limits"
        }
    ],
    "PAT002": [
        {
            "test_name": "TSH",
            "value": "2.5",
            "unit": "mIU/L",
            "reference_range": "0.4-4.0",
            "status": "final",
            "abnormal_flag": "",
            "collection_date": "2025-01-10",
            "result_date": "2025-01-10", 
            "ordering_provider": "Dr. Jones",
            "notes": "Normal thyroid function"
        }
    ],
    "PAT003": [
        {
            "test_name": "Troponin I",
            "value": "0.02",
            "unit": "ng/mL",
            "reference_range": "<0.04",
            "status": "final",
            "abnormal_flag": "",
            "collection_date": "2025-01-20",
            "result_date": "2025-01-20",
            "ordering_provider": "Dr. Brown", 
            "notes": "Normal cardiac enzymes"
        }
    ]
}

@mcp.tool(description="Get patient demographic information by patient ID")
def get_patient_info(patient_id: str) -> Dict:
    """Retrieve patient demographic information."""
    if patient_id not in SAMPLE_PATIENTS:
        return {"error": f"Patient {patient_id} not found"}
    
    return SAMPLE_PATIENTS[patient_id]

@mcp.tool(description="Get complete medical history for a patient")
def get_patient_history(patient_id: str) -> Dict:
    """Retrieve complete medical history for a patient."""
    if patient_id not in SAMPLE_PATIENTS:
        return {"error": f"Patient {patient_id} not found"}
    
    history = SAMPLE_MEDICAL_HISTORY.get(patient_id, [])
    return {
        "patient_id": patient_id,
        "medical_history": history,
        "total_conditions": len(history)
    }

@mcp.tool(description="Get lab results for a patient within specified timeframe")
def get_lab_results(patient_id: str, days_back: int = 365) -> Dict:
    """Retrieve lab results for a patient within specified timeframe."""
    if patient_id not in SAMPLE_PATIENTS:
        return {"error": f"Patient {patient_id} not found"}
    
    lab_results = SAMPLE_LAB_RESULTS.get(patient_id, [])
    
    # Filter by date range (simplified for sample data)
    cutoff_date = datetime.now() - timedelta(days=days_back)
    filtered_results = []
    
    for result in lab_results:
        result_date = datetime.strptime(result["collection_date"], "%Y-%m-%d")
        if result_date >= cutoff_date:
            filtered_results.append(result)
    
    return {
        "patient_id": patient_id,
        "lab_results": filtered_results,
        "total_results": len(filtered_results),
        "date_range": f"Last {days_back} days"
    }

@mcp.tool(description="Search for patients by name or ID")
def search_patients(query: str) -> Dict:
    """Search for patients by name or patient ID."""
    results = []
    query_lower = query.lower()
    
    for patient_id, patient_data in SAMPLE_PATIENTS.items():
        if (query_lower in patient_id.lower() or 
            query_lower in patient_data["name"].lower()):
            results.append({
                "patient_id": patient_id,
                "name": patient_data["name"],
                "date_of_birth": patient_data["date_of_birth"],
                "gender": patient_data["gender"]
            })
    
    return {
        "query": query,
        "results": results,
        "total_found": len(results)
    }

@mcp.tool(description="Get comprehensive patient summary including demographics, history, and recent labs")
def get_patient_summary(patient_id: str, include_labs_days: int = 365) -> Dict:
    """Get comprehensive patient summary."""
    if patient_id not in SAMPLE_PATIENTS:
        return {"error": f"Patient {patient_id} not found"}
    
    # Get all patient data
    patient_info = SAMPLE_PATIENTS[patient_id]
    medical_history = SAMPLE_MEDICAL_HISTORY.get(patient_id, [])
    lab_results = SAMPLE_LAB_RESULTS.get(patient_id, [])
    
    # Filter recent lab results
    cutoff_date = datetime.now() - timedelta(days=include_labs_days)
    recent_labs = []
    for result in lab_results:
        result_date = datetime.strptime(result["collection_date"], "%Y-%m-%d")
        if result_date >= cutoff_date:
            recent_labs.append(result)
    
    # Get active conditions
    active_conditions = [h for h in medical_history if h["status"].lower() == "active"]
    
    # Generate summary
    summary = {
        "patient_info": patient_info,
        "active_conditions": active_conditions,
        "recent_lab_results": recent_labs,
        "summary_stats": {
            "total_conditions": len(medical_history),
            "active_conditions": len(active_conditions),
            "recent_lab_count": len(recent_labs)
        },
        "risk_factors": _generate_risk_factors(active_conditions, recent_labs),
        "summary_generated": datetime.now().isoformat()
    }
    
    return summary

def _generate_risk_factors(conditions: List[Dict], lab_results: List[Dict]) -> List[str]:
    """Generate risk factors based on conditions and lab results."""
    risk_factors = []
    
    # Check conditions
    condition_names = [c["condition"].lower() for c in conditions]
    if any("diabetes" in name for name in condition_names):
        risk_factors.append("Diabetes - requires ongoing monitoring")
    if any("hypertension" in name for name in condition_names):
        risk_factors.append("Hypertension - cardiovascular risk factor")
    if any("coronary" in name or "heart" in name for name in condition_names):
        risk_factors.append("Cardiovascular disease - high risk")
    
    # Check lab results
    for lab in lab_results:
        if lab["abnormal_flag"] == "H":
            if "glucose" in lab["test_name"].lower():
                risk_factors.append("Elevated glucose levels")
            elif "cholesterol" in lab["test_name"].lower():
                risk_factors.append("High cholesterol levels")
            elif "hba1c" in lab["test_name"].lower():
                risk_factors.append("Poor diabetes control")
    
    return list(set(risk_factors))  # Remove duplicates

mcp.run(transport="streamable-http")