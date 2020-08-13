## stockbets.io frontend README

#### Import notes
* We use a wrapped version of axios for API posts that re-routes all 400 code responses back to the login page. There are more elegant ways to do this, but for now it's a hack for managing session auth that works well enough. Effectively, API code 400 is a reserved code strictly for non-authenticated access tempts to the apps pages. 