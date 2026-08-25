---
layout: archive
title: "Sitemap"
permalink: /sitemap/
author_profile: true
---

{% include base_path %}

A curated guide to the pages and collections on this site.

<nav aria-label="Sitemap">
  <section>
    <h2>Main</h2>
    <ul>
      <li><a href="{{ base_path }}/">Home</a></li>
      <li><a href="{{ base_path }}/cv/">CV</a></li>
    </ul>
  </section>

  <section>
    <h2>Academic</h2>
    <ul>
      <li><a href="{{ base_path }}/projects/">Projects overview</a></li>
      {% assign academic_items = site.presentations | concat: site.posters | sort: "date" | reverse %}
      {% for post in academic_items %}
        {% if post.title and post.sitemap != false %}
          <li>
            <a href="{{ base_path }}{{ post.url }}">{{ post.title }}</a>
            {% if post.date %}<small>({{ post.date | date: "%Y" }})</small>{% endif %}
          </li>
        {% endif %}
      {% endfor %}
    </ul>
  </section>

  <section>
    <h2>Travel</h2>
    <ul>
      <li><a href="{{ base_path }}/travel/">Travel Log overview</a></li>
      {% assign travel_items = site.travel | sort: "date" | reverse %}
      {% for post in travel_items %}
        {% if post.title and post.sitemap != false %}
          <li>
            <a href="{{ base_path }}{{ post.url }}">{{ post.title }}</a>
            {% if post.date %}<small>({{ post.date | date: "%Y" }})</small>{% endif %}
          </li>
        {% endif %}
      {% endfor %}
    </ul>
  </section>

  <section>
    <h2>Memories</h2>
    <ul>
      <li><a href="{{ base_path }}/memories/">Memories overview</a></li>
      {% assign memory_items = site.memories | sort: "date" | reverse %}
      {% for post in memory_items %}
        {% if post.title and post.sitemap != false %}
          <li>
            <a href="{{ base_path }}{{ post.url }}">{{ post.title }}</a>
            {% if post.date %}<small>({{ post.date | date: "%Y" }})</small>{% endif %}
          </li>
        {% endif %}
      {% endfor %}
    </ul>
  </section>

  <section>
    <h2>Site Information</h2>
    <ul>
      <li><a href="{{ base_path }}/terms/">Terms and Privacy Policy</a></li>
      <li><a href="{{ base_path }}/sitemap.xml">XML sitemap</a></li>
    </ul>
  </section>
</nav>
