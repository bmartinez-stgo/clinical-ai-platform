{{- define "ocr-engine.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "ocr-engine.fullname" -}}
{{- printf "%s" .Chart.Name -}}
{{- end -}}

{{- define "ocr-engine.labels" -}}
app.kubernetes.io/name: {{ include "ocr-engine.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.app.serviceVersion | quote }}
app.kubernetes.io/component: api
app.kubernetes.io/part-of: clinical-ai-platform
{{- end -}}

{{- define "ocr-engine.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ocr-engine.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
