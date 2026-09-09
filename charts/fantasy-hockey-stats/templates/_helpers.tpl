{{- define "fantasy-hockey-stats.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "fantasy-hockey-stats.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name (include "fantasy-hockey-stats.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "fantasy-hockey-stats.labels" -}}
app.kubernetes.io/name: {{ include "fantasy-hockey-stats.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | quote }}
{{- end }}

{{- define "fantasy-hockey-stats.selectorLabels" -}}
app.kubernetes.io/name: {{ include "fantasy-hockey-stats.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "fantasy-hockey-stats.dataClaimName" -}}
{{- default (printf "%s-data" (include "fantasy-hockey-stats.fullname" .)) .Values.persistence.existingClaim }}
{{- end }}
