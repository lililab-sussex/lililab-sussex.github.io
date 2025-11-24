---
title: Team
nav:
  order: 3
  tooltip: About our team
---

# {% include icon.html icon="fa-solid fa-users" %}Team

{% include list.html data="members" component="portrait" filter="role == 'pi'" %}
{% include list.html data="members" component="portrait" filter="role != 'pi'" %}

{% include section.html %}

{% include figure.html image="images/photos/album.jpg" caption="LILI Lab" width="100%" %}

Members of our lab include PIs, students, and collaborators from multidisciplinary backgrounds, working together across imaging, vision, ecology, and core machine learning, with a focus on interpretable modelling.
