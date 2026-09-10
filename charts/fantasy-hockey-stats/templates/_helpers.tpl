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

{{- define "fantasy-hockey-stats.databaseSecretName" -}}
{{- required "database.existingSecret is required" .Values.database.existingSecret }}
{{- end }}

{{- define "fantasy-hockey-stats.databaseUrlEnv" -}}
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: {{ include "fantasy-hockey-stats.databaseSecretName" . }}
      key: {{ .Values.database.secretKey }}
{{- end }}

{{- define "fantasy-hockey-stats.webNginxConfig" -}}
server {
    listen 8080;
    server_name _;
    root /usr/share/nginx/html;
    index 200.html;

    location /api/ {
        proxy_pass http://{{ include "fantasy-hockey-stats.fullname" . }}-api:{{ .Values.api.service.port }};
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /200.html;
    }
}
{{- end }}
