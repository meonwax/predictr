'use strict';

angular.module('predictrApp')
  .constant("ROLES", {
    "ADMIN": "ROLE_ADMIN",
    "USER": "ROLE_USER"
  })
  .constant('angularMomentConfig', {
    timezone: 'Europe/Berlin'
  });
