// Patient, appointment, and call types

export interface Patient {
  id: string;
  clinic_id: string;
  ehr_patient_id: string | null;
  first_name: string;
  last_name: string;
  date_of_birth: string | null;
  phone: string | null;
  email: string | null;
  insurance_carrier: string | null;
  insurance_member_id: string | null;
  uninsured: boolean;
  created_at: string;
}

export type AppointmentStatus =
  | "scheduled"
  | "confirmed"
  | "completed"
  | "cancelled"
  | "no_show";

export interface Appointment {
  id: string;
  clinic_id: string;
  patient_id: string;
  patient_name?: string;
  ehr_appointment_id: string | null;
  provider_id: string | null;
  provider_name: string | null;
  appointment_datetime: string;
  duration_minutes: number;
  reason: string | null;
  status: AppointmentStatus;
  booked_by_agent: string;
  call_id: string | null;
  created_at: string;
}

export interface Call {
  id: string;
  clinic_id: string;
  patient_id: string | null;
  patient_name?: string;
  retell_call_id: string | null;
  call_type: "inbound" | "outbound";
  from_number: string | null;
  duration_ms: number | null;
  intent: string | null;
  outcome: string | null;
  agent_type: string;
  started_at: string;
  ended_at: string | null;
}

export interface CallTranscriptTurn {
  role: "agent" | "user";
  content: string;
  timestamp?: string;
}
