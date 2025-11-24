---
title: Contact
nav:
  order: 5
  tooltip: Emails, address, and location
---

# {% include icon.html icon="fa-regular fa-envelope" %}Contact

<div class="contact-grid">
  <div class="contact-card">
    {% include figure.html image="images/team-photos/Ivor.jpg" caption="Email Ivor Simpson:" width="80px" %}
    {%
      include button.html
      type="Ivor Simpson Email"
      text="I.Simpson@sussex.ac.uk"
      link="I.Simpson@sussex.ac.uk"
      style="secondary"
    %}
  </div>
  <div class="contact-card">
    {% include figure.html image="images/team-photos/Peter.jpeg" caption="Email Peter Wijeratne:" width="80px" %}
    {%
      include button.html
      type="Peter Wijeratne Email"
      text="P.Wijeratne@sussex.ac.uk"
      link="P.Wijeratne@sussex.ac.uk"
      style="secondary"
    %}
  </div>
  <div class="contact-card">
    {% include figure.html image="images/icon.png" caption="Find our Lab:" width="80px" %}
    {%
      include button.html
      type="address"
      tooltip="Our location on Google Maps for easy navigation"
      link="https://www.google.com/maps"
      style="secondary"
    %}
  </div>
</div>
