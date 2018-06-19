'use strict';

angular.module('predictrApp')
  .directive('focusMe', function($timeout) {
    return {
      restrict: 'A',
      scope: {
        trigger: '@focusMe'
      },
      link: function(scope, element) {
        scope.$watch('trigger', function(value) {
          if (value === 'true') {
            $timeout(function() {
              element[0].focus();
            });
          }
        });
      }
    };
  })
  .directive('validateCompareTo', function() {
    return {
      restrict: 'A',
      require: 'ngModel',
      scope: {
        otherModelValue: "=validateCompareTo"
      },
      link: function(scope, element, attributes, ngModel) {
        ngModel.$validators.compareTo = function(modelValue) {
          return modelValue == scope.otherModelValue;
        };
        scope.$watch("otherModelValue", function() {
          ngModel.$validate();
        });
      }
    };
  })
  .directive('myBet', function() {
    return {
      restrict: 'A',
      require: 'ngModel',
      link: function(scope, element, attributes, ngModel) {

        function formatter(value) {
          if (value) {
            return value.scoreHome + ':' + value.scoreAway;
          }
        }
        ngModel.$formatters.push(formatter);

        function parser(value) {
          if (value) {
            var arr = value.split(':');
            if (arr.length == 2 && arr[0] && arr[1]) {
              var bet = {};
              bet.scoreHome = arr[0];
              bet.scoreAway = arr[1];
              bet.game = scope.$parent.game;
              return bet;
            }
          }
          return '';
        }
        ngModel.$parsers.push(parser);
      }
    };
  });
