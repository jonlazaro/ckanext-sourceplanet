CKAN SourcePlanet Extension
========================

**Status:** Alpha

**CKAN Version:** 1.8

The aim of SourcePlanet project is using CKAN for managing Open Source Software Projects' metadata. For that purpouse, SourcePlanet manages three entities identifying:
- Open Source Projects (project)
- Open Source Products (product)
- Organizations / Companies (organization)

As CKAN Dataset/Package model is basically based on project-like models, SourcePlanet uses that entity for "Project"s and "Product"s (with some modifications).
"Organization"s support is based on ckanext-organizations extensions provided by CKAN by default.

This extension provides CKAN customization for SourcePlanet project with functionalities like:
- New entitites project and product instead of dataset entity.
- New forms for projects and products.
- Quality related info in project and producs.
- New interface according to SourcePlanet needs.
- Modified RDF descriptions adapted to software project descriptions (using DOAP ontology).
