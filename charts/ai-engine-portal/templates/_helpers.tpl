{{- define "ai-engine-portal.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "ai-engine-portal.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- include "ai-engine-portal.name" . -}}
{{- end -}}
{{- end -}}

{{- define "ai-engine-portal.labels" -}}
app.kubernetes.io/name: {{ include "ai-engine-portal.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/component: ui
app.kubernetes.io/part-of: clinical-ai-platform
{{- end -}}

{{- define "ai-engine-portal.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ai-engine-portal.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
