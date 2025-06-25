# Markdown Report Template with Static Logo

<div align="center">

![Logo Municipal](/Citoyen/static/municipal_logo.jpg)

# RAPPORT MUNICIPAL
## Municipalité de {{ municipality_name }}

---

**Période d'analyse:** {{ period_text }}  
**Généré le:** {{ generated_date }}  
**Généré par:** Système de gestion municipale Belediyti

</div>

---

## RÉSUMÉ EXÉCUTIF

### Vue d'ensemble
Ce rapport présente une analyse complète de l'activité de signalement pour la municipalité de **{{ municipality_name }}** {{ period_text }}. Au total, **{{ total_issues }} signalements** ont été analysés, révélant un taux de résolution de **{{ resolution_rate }}%**.

### Indicateurs Clés de Performance

| Indicateur | Valeur | Statut |
|------------|--------|--------|
| Total des signalements | {{ total_issues }} | {{ total_status }} |
| Taux de résolution | {{ resolution_rate }}% | {{ resolution_status }} |
| Signalements en attente | {{ pending_issues }} | {{ pending_status }} |
| Temps moyen de résolution | {{ avg_resolution_time }} jours | {{ resolution_time_status }} |

### Points Clés
{% for finding in key_findings %}
- {{ finding }}
{% endfor %}

### Recommandations
{% for recommendation in recommendations %}
- {{ recommendation }}
{% endfor %}

---

## ANALYSE DES PROBLÈMES

### Statistiques Générales
- **Total des problèmes signalés:** {{ problems_total }}
- **Problèmes résolus:** {{ problems_resolved }} ({{ problems_resolution_rate }}%)
- **Problèmes en attente:** {{ problems_pending }}
- **Problèmes en cours:** {{ problems_in_progress }}

### Répartition par Statut
{% for status in problems_by_status %}
- **{{ status.status }}:** {{ status.count }} signalements
{% endfor %}

### Répartition par Catégorie
{% for category in problems_by_category %}
- **{{ category.name }}:** {{ category.count }} signalements
{% endfor %}

### Analyse des Temps de Résolution
- **Temps moyen de résolution:** {{ avg_resolution_time }} jours
- **Résolution la plus rapide:** {{ fastest_resolution }} jours
- **Résolution la plus lente:** {{ slowest_resolution }} jours

#### Temps de Résolution par Catégorie
{% for category in resolution_by_category %}
- **{{ category.category }}:** {{ category.avg_days }} jours ({{ category.count }} problèmes)
{% endfor %}

### Analyse des Priorités
- **Haute priorité (< 7 jours):** {{ high_priority }} problèmes
- **Moyenne priorité (7-30 jours):** {{ medium_priority }} problèmes
- **Basse priorité (> 30 jours):** {{ low_priority }} problèmes

---

## ANALYSE DES RÉCLAMATIONS

### Statistiques Générales
- **Total des réclamations:** {{ complaints_total }}
- **Réclamations résolues:** {{ complaints_resolved }}
- **Réclamations en attente:** {{ complaints_pending }}
- **Réclamations en examen:** {{ complaints_reviewing }}

### Répartition par Statut
{% for status in complaints_by_status %}
- **{{ status.status }}:** {{ status.count }} réclamations
{% endfor %}

### Analyse des Temps de Réponse
- **Temps moyen de réponse:** {{ avg_response_time }} jours
- **Réponse la plus rapide:** {{ min_response_time }} jours
- **Réponse la plus lente:** {{ max_response_time }} jours

---

## ÉVOLUTION TEMPORELLE

### Tendances Générales
- **Évolution des problèmes:** {{ problems_trend }}% par rapport à la période précédente
- **Évolution des réclamations:** {{ complaints_trend }}% par rapport à la période précédente

### Moyennes Quotidiennes
- **Problèmes par jour:** {{ daily_avg_problems }}
- **Réclamations par jour:** {{ daily_avg_complaints }}

---

## DISTRIBUTION GÉOGRAPHIQUE

### Analyse Spatiale
{% if geographic_data %}
Les problèmes signalés sont répartis sur {{ geographic_locations_count }} emplacements différents dans la municipalité. La concentration la plus élevée se trouve dans les zones urbaines centrales.

#### Répartition par Zone
{% for zone in geographic_zones %}
- **{{ zone.name }}:** {{ zone.count }} signalements
{% endfor %}
{% else %}
Aucune donnée géographique disponible pour cette période.
{% endif %}

---

## PROBLÈMES RÉCENTS

### Derniers Signalements
{% for problem in recent_problems %}
**{{ problem.id }}** - {{ problem.created_at }}
- **Description:** {{ problem.description }}
- **Localisation:** {{ problem.location }}
- **Catégorie:** {{ problem.category }}
- **Statut:** {{ problem.status }}

{% endfor %}

---

## RÉCLAMATIONS RÉCENTES

### Dernières Réclamations
{% for complaint in recent_complaints %}
**{{ complaint.id }}** - {{ complaint.created_at }}
- **Sujet:** {{ complaint.subject }}
- **Description:** {{ complaint.description }}
- **Statut:** {{ complaint.status }}

{% endfor %}

---

## INSIGHTS ET ANALYSES

### Observations Clés
{% for insight in insights %}
- {{ insight }}
{% endfor %}

### Comparaison avec la Période Précédente
{% if has_comparison_data %}
- **Problèmes:** {{ current_problems }} vs {{ previous_problems }} ({{ problems_change }}%)
- **Réclamations:** {{ current_complaints }} vs {{ previous_complaints }} ({{ complaints_change }}%)
- **Taux de résolution:** {{ current_resolution_rate }}% vs {{ previous_resolution_rate }}%
{% else %}
Données de comparaison non disponibles pour cette période.
{% endif %}

---

## RECOMMANDATIONS STRATÉGIQUES

### Actions Prioritaires
{% for action in priority_actions %}
1. {{ action }}
{% endfor %}

### Améliorations Suggérées
{% for improvement in suggested_improvements %}
- {{ improvement }}
{% endfor %}

### Suivi et Monitoring
{% for monitoring in monitoring_points %}
- {{ monitoring }}
{% endfor %}

---

## ANNEXES

### Méthodologie
Ce rapport a été généré automatiquement à partir des données du système de gestion municipale. Les calculs incluent :
- Analyse statistique descriptive
- Calculs de tendances et variations
- Analyse géospatiale des signalements
- Évaluation des temps de traitement

### Définitions
- **Taux de résolution:** Pourcentage de signalements résolus par rapport au total
- **Temps de résolution:** Délai entre la création et la résolution d'un signalement
- **Haute priorité:** Signalements en attente depuis moins de 7 jours
- **Moyenne priorité:** Signalements en attente entre 7 et 30 jours
- **Basse priorité:** Signalements en attente depuis plus de 30 jours

### Contact
Pour toute question concernant ce rapport, veuillez contacter l'administration municipale de {{ municipality_name }}.

---

<div align="center">

![Logo Municipal](/Citoyen/static/municipal_logo.jpg)

*Rapport généré automatiquement par le système de gestion municipale Belediyti*  
*{{ generated_date }}*

</div>