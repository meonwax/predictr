'use strict';

angular.module('predictrApp')
  .factory('User', function($q, $http, $resource) {
    return {
      account: function() {
        return $resource('api/users/account');
      },
      register: function() {
        return $resource('api/users/register');
      },
      changePassword: function() {
        return $resource('api/users/password/change');
      },
      resetPassword: function() {
        return $resource('api/users/password/resetRequest');
      },
      avatar: function(contentType) {
        return $resource('api/users/avatar', {}, {
          'save': {
            method: 'POST',
            headers: {'Content-Type': contentType},
            transformRequest: []
          }
        });
      },
      all: function() {
        return $resource('api/users', {}, {
          'query': {
            method: 'GET',
            isArray: true
          }
        });
      },
    };
  });
