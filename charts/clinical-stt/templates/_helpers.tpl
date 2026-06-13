{{- define "clinical-stt.name" -}}
{{- .Chart.Name }}
{{- end }}

{{- define "clinical-stt.fullname" -}}
{{- .Chart.Name }}
{{- end }}

{{- define "clinical-stt.labels" -}}
app.kubernetes.io/name: {{ include "clinical-stt.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}

{{- define "clinical-stt.selectorLabels" -}}
app.kubernetes.io/name: {{ include "clinical-stt.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
