{{- define "vision-inference.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "vision-inference.fullname" -}}
{{- printf "%s" .Chart.Name -}}
{{- end -}}

{{- define "vision-inference.labels" -}}
app.kubernetes.io/name: {{ include "vision-inference.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.app.serviceVersion | quote }}
app.kubernetes.io/component: api
app.kubernetes.io/part-of: clinical-ai-platform
{{- end -}}

{{- define "vision-inference.selectorLabels" -}}
app.kubernetes.io/name: {{ include "vision-inference.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
