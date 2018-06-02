'use strict';

angular.module('predictrApp')
  .factory('HttpInterceptorService', function($rootScope, $q) {
    return {
      responseError: function(rejection) {
        if (rejection.status == 401) {
          $rootScope.logout();
        }
        // TODO: Handle AJAX errors here
        return $q.reject(rejection);
      }
    };
  });
