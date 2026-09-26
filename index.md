---
layout: home
title: Home
---

# Welcome to Tech Gear Pulse

Explore our daily automated deal roundups, technical reviews, and buyer guides below:

## Latest Articles
{% for post in site.posts %}
* [{{ post.title }}]({{ post.url | relative_url }}) - {{ post.date | date: "%B %d, %Y" }}
{% endfor %}
