'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    $routeProvider.when('/shoutbox', {
      templateUrl: 'templates/shoutbox.html',
      controller: 'ShoutboxCtrl',
      activeTab: 'shoutbox',
      resolve: {
        shouts: function($q, Shout, $rootScope) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          Shout.query({limit: 15}, function(shouts) {
            deferred.resolve(shouts);
          });
          return deferred.promise;
        }
      }
    });
  });
