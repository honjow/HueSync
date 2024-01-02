(function (React) {
    'use strict';

    function _interopDefaultLegacy (e) { return e && typeof e === 'object' && 'default' in e ? e : { 'default': e }; }

    var React__default = /*#__PURE__*/_interopDefaultLegacy(React);

    let webpackCache = {};
    let hasWebpack5 = false;
    if (window.webpackJsonp && !window.webpackJsonp.deckyShimmed) {
        // Webpack 4, currently on stable
        const wpRequire = window.webpackJsonp.push([
            [],
            { get_require: (mod, _exports, wpRequire) => (mod.exports = wpRequire) },
            [['get_require']],
        ]);
        delete wpRequire.m.get_require;
        delete wpRequire.c.get_require;
        webpackCache = wpRequire.c;
    }
    else {
        // Webpack 5, currently on beta
        hasWebpack5 = true;
        const id = Math.random();
        let initReq;
        window.webpackChunksteamui.push([
            [id],
            {},
            (r) => {
                initReq = r;
            },
        ]);
        for (let i of Object.keys(initReq.m)) {
            try {
                webpackCache[i] = initReq(i);
            }
            catch (e) {
                console.debug("[DFL:Webpack]: Ignoring require error for module", i, e);
            }
        }
    }
    const allModules = hasWebpack5
        ? Object.values(webpackCache).filter((x) => x)
        : Object.keys(webpackCache)
            .map((x) => webpackCache[x].exports)
            .filter((x) => x);
    const findModule = (filter) => {
        for (const m of allModules) {
            if (m.default && filter(m.default))
                return m.default;
            if (filter(m))
                return m;
        }
    };
    const findModuleChild = (filter) => {
        for (const m of allModules) {
            for (const mod of [m.default, m]) {
                const filterRes = filter(mod);
                if (filterRes) {
                    return filterRes;
                }
                else {
                    continue;
                }
            }
        }
    };
    const CommonUIModule = allModules.find((m) => {
        if (typeof m !== 'object')
            return false;
        for (let prop in m) {
            if (m[prop]?.contextType?._currentValue && Object.keys(m).length > 60)
                return true;
        }
        return false;
    });
    findModule((m) => {
        if (typeof m !== 'object')
            return false;
        for (let prop in m) {
            if (m[prop]?.toString && /Spinner\)}\),.\.createElement\(\"path\",{d:\"M18 /.test(m[prop].toString()))
                return true;
        }
        return false;
    });
    allModules.find((m) => {
        if (typeof m !== 'object')
            return undefined;
        for (let prop in m) {
            if (m[prop]?.computeRootMatch)
                return true;
        }
        return false;
    });

    findModuleChild((mod) => {
        if (typeof mod !== 'object' || !mod.__esModule)
            return undefined;
        return mod.Panel;
    });
    const [panelSection, mod] = findModuleChild((mod) => {
        for (let prop in mod) {
            if (mod[prop]?.toString()?.includes('.PanelSection')) {
                return [mod[prop], mod];
            }
        }
        return null;
    });
    const PanelSection = panelSection;
    // New as of Feb 22 2023 Beta || Old
    const PanelSectionRow = mod.PanelSectionRow ||
        Object.values(mod).filter((exp) => !exp?.toString()?.includes('.PanelSection'))[0];

    const SliderField = Object.values(CommonUIModule).find((mod) => mod?.toString()?.includes('SliderField,fallback'));

    const quickAccessMenuClasses = findModule((mod) => typeof mod === 'object' && mod?.Title?.includes('quickaccessmenu'));
    /**
     * @depreciated please use quickAccessMenuClasses instead
     */
    const staticClasses = quickAccessMenuClasses;
    findModule((mod) => typeof mod === 'object' && mod?.ScrollPanel?.includes('scrollpanel'));
    findModule((mod) => typeof mod === 'object' && mod?.GamepadDialogContent?.includes('gamepaddialog'));
    findModule((mod) => typeof mod === 'object' && typeof mod?.PanelSection === 'string' && mod?.PanelSection?.includes('quickaccesscontrols'));
    findModule((mod) => typeof mod === 'object' && mod?.OOBEUpdateStatusContainer?.includes('updaterfield'));
    findModule((mod) => typeof mod === 'object' && mod?.Container?.includes('appdetailsplaysection'));
    findModule((mod) => typeof mod === 'object' && mod?.SliderControlPanelGroup?.includes('gamepadslider'));
    findModule((mod) => typeof mod === 'object' && mod?.TopCapsule?.includes('sharedappdetailsheader'));
    findModule((mod) => typeof mod === 'object' && mod?.HeaderLoaded?.includes('appdetails_'));
    findModule((mod) => typeof mod === 'object' && mod?.BasicUiRoot?.includes('gamepadui_'));
    findModule((mod) => typeof mod === 'object' && mod?.GamepadTabbedPage?.includes('gamepadtabbedpage_'));
    findModule((mod) => typeof mod === 'object' && mod?.BasicContextMenuModal?.includes('gamepadcontextmenu'));
    findModule((mod) => typeof mod === 'object' && mod?.AchievementListItemBase?.includes('achievementslist'));
    findModule((mod) => typeof mod === 'object' && mod?.MainMenuAppRunning?.includes('mainmenuapprunning'));
    findModule((mod) => typeof mod === 'object' && mod?.AppDetailsRoot?.includes('basicappdetailssectionstyler_'));

    const ToggleField = Object.values(CommonUIModule).find((mod) => mod?.render?.toString()?.includes('ToggleField,fallback'));

    // TypeScript helper function
    const definePlugin = (fn) => {
        return (...args) => {
            // TODO: Maybe wrap this
            return fn(...args);
        };
    };

    var DefaultContext = {
      color: undefined,
      size: undefined,
      className: undefined,
      style: undefined,
      attr: undefined
    };
    var IconContext = React__default["default"].createContext && React__default["default"].createContext(DefaultContext);

    var __assign$1 = window && window.__assign || function () {
      __assign$1 = Object.assign || function (t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
          s = arguments[i];

          for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p)) t[p] = s[p];
        }

        return t;
      };

      return __assign$1.apply(this, arguments);
    };

    var __rest = window && window.__rest || function (s, e) {
      var t = {};

      for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0) t[p] = s[p];

      if (s != null && typeof Object.getOwnPropertySymbols === "function") for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
        if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i])) t[p[i]] = s[p[i]];
      }
      return t;
    };

    function Tree2Element(tree) {
      return tree && tree.map(function (node, i) {
        return React__default["default"].createElement(node.tag, __assign$1({
          key: i
        }, node.attr), Tree2Element(node.child));
      });
    }

    function GenIcon(data) {
      return function (props) {
        return React__default["default"].createElement(IconBase, __assign$1({
          attr: __assign$1({}, data.attr)
        }, props), Tree2Element(data.child));
      };
    }
    function IconBase(props) {
      var elem = function (conf) {
        var attr = props.attr,
            size = props.size,
            title = props.title,
            svgProps = __rest(props, ["attr", "size", "title"]);

        var computedSize = size || conf.size || "1em";
        var className;
        if (conf.className) className = conf.className;
        if (props.className) className = (className ? className + ' ' : '') + props.className;
        return React__default["default"].createElement("svg", __assign$1({
          stroke: "currentColor",
          fill: "currentColor",
          strokeWidth: "0"
        }, conf.attr, attr, svgProps, {
          className: className,
          style: __assign$1(__assign$1({
            color: props.color || conf.color
          }, conf.style), props.style),
          height: computedSize,
          width: computedSize,
          xmlns: "http://www.w3.org/2000/svg"
        }), title && React__default["default"].createElement("title", null, title), props.children);
      };

      return IconContext !== undefined ? React__default["default"].createElement(IconContext.Consumer, null, function (conf) {
        return elem(conf);
      }) : elem(DefaultContext);
    }

    // THIS FILE IS AUTO GENERATED
    function FaLightbulb (props) {
      return GenIcon({"tag":"svg","attr":{"viewBox":"0 0 352 512"},"child":[{"tag":"path","attr":{"d":"M96.06 454.35c.01 6.29 1.87 12.45 5.36 17.69l17.09 25.69a31.99 31.99 0 0 0 26.64 14.28h61.71a31.99 31.99 0 0 0 26.64-14.28l17.09-25.69a31.989 31.989 0 0 0 5.36-17.69l.04-38.35H96.01l.05 38.35zM0 176c0 44.37 16.45 84.85 43.56 115.78 16.52 18.85 42.36 58.23 52.21 91.45.04.26.07.52.11.78h160.24c.04-.26.07-.51.11-.78 9.85-33.22 35.69-72.6 52.21-91.45C335.55 260.85 352 220.37 352 176 352 78.61 272.91-.3 175.45 0 73.44.31 0 82.97 0 176zm176-80c-44.11 0-80 35.89-80 80 0 8.84-7.16 16-16 16s-16-7.16-16-16c0-61.76 50.24-112 112-112 8.84 0 16 7.16 16 16s-7.16 16-16 16z"}}]})(props);
    }

    /******************************************************************************
    Copyright (c) Microsoft Corporation.

    Permission to use, copy, modify, and/or distribute this software for any
    purpose with or without fee is hereby granted.

    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
    REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
    AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
    INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
    LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
    OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
    PERFORMANCE OF THIS SOFTWARE.
    ***************************************************************************** */

    var __assign = function() {
        __assign = Object.assign || function __assign(t) {
            for (var s, i = 1, n = arguments.length; i < n; i++) {
                s = arguments[i];
                for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p)) t[p] = s[p];
            }
            return t;
        };
        return __assign.apply(this, arguments);
    };

    function __decorate(decorators, target, key, desc) {
        var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
        if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
        else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
        return c > 3 && r && Object.defineProperty(target, key, r), r;
    }

    function __metadata(metadataKey, metadataValue) {
        if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(metadataKey, metadataValue);
    }

    function __spreadArray(to, from, pack) {
        if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
            if (ar || !(i in from)) {
                if (!ar) ar = Array.prototype.slice.call(from, 0, i);
                ar[i] = from[i];
            }
        }
        return to.concat(ar || Array.prototype.slice.call(from));
    }

    var commonjsGlobal = typeof globalThis !== 'undefined' ? globalThis : typeof window !== 'undefined' ? window : typeof global !== 'undefined' ? global : typeof self !== 'undefined' ? self : {};

    /*! *****************************************************************************
    Copyright (C) Microsoft. All rights reserved.
    Licensed under the Apache License, Version 2.0 (the "License"); you may not use
    this file except in compliance with the License. You may obtain a copy of the
    License at http://www.apache.org/licenses/LICENSE-2.0

    THIS CODE IS PROVIDED ON AN *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED
    WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
    MERCHANTABLITY OR NON-INFRINGEMENT.

    See the Apache Version 2.0 License for specific language governing permissions
    and limitations under the License.
    ***************************************************************************** */

    var Reflect$1;
    (function (Reflect) {
        // Metadata Proposal
        // https://rbuckton.github.io/reflect-metadata/
        (function (factory) {
            var root = typeof commonjsGlobal === "object" ? commonjsGlobal :
                typeof self === "object" ? self :
                    typeof this === "object" ? this :
                        Function("return this;")();
            var exporter = makeExporter(Reflect);
            if (typeof root.Reflect === "undefined") {
                root.Reflect = Reflect;
            }
            else {
                exporter = makeExporter(root.Reflect, exporter);
            }
            factory(exporter);
            function makeExporter(target, previous) {
                return function (key, value) {
                    if (typeof target[key] !== "function") {
                        Object.defineProperty(target, key, { configurable: true, writable: true, value: value });
                    }
                    if (previous)
                        previous(key, value);
                };
            }
        })(function (exporter) {
            var hasOwn = Object.prototype.hasOwnProperty;
            // feature test for Symbol support
            var supportsSymbol = typeof Symbol === "function";
            var toPrimitiveSymbol = supportsSymbol && typeof Symbol.toPrimitive !== "undefined" ? Symbol.toPrimitive : "@@toPrimitive";
            var iteratorSymbol = supportsSymbol && typeof Symbol.iterator !== "undefined" ? Symbol.iterator : "@@iterator";
            var supportsCreate = typeof Object.create === "function"; // feature test for Object.create support
            var supportsProto = { __proto__: [] } instanceof Array; // feature test for __proto__ support
            var downLevel = !supportsCreate && !supportsProto;
            var HashMap = {
                // create an object in dictionary mode (a.k.a. "slow" mode in v8)
                create: supportsCreate
                    ? function () { return MakeDictionary(Object.create(null)); }
                    : supportsProto
                        ? function () { return MakeDictionary({ __proto__: null }); }
                        : function () { return MakeDictionary({}); },
                has: downLevel
                    ? function (map, key) { return hasOwn.call(map, key); }
                    : function (map, key) { return key in map; },
                get: downLevel
                    ? function (map, key) { return hasOwn.call(map, key) ? map[key] : undefined; }
                    : function (map, key) { return map[key]; },
            };
            // Load global or shim versions of Map, Set, and WeakMap
            var functionPrototype = Object.getPrototypeOf(Function);
            var usePolyfill = typeof process === "object" && process.env && process.env["REFLECT_METADATA_USE_MAP_POLYFILL"] === "true";
            var _Map = !usePolyfill && typeof Map === "function" && typeof Map.prototype.entries === "function" ? Map : CreateMapPolyfill();
            var _Set = !usePolyfill && typeof Set === "function" && typeof Set.prototype.entries === "function" ? Set : CreateSetPolyfill();
            var _WeakMap = !usePolyfill && typeof WeakMap === "function" ? WeakMap : CreateWeakMapPolyfill();
            // [[Metadata]] internal slot
            // https://rbuckton.github.io/reflect-metadata/#ordinary-object-internal-methods-and-internal-slots
            var Metadata = new _WeakMap();
            /**
             * Applies a set of decorators to a property of a target object.
             * @param decorators An array of decorators.
             * @param target The target object.
             * @param propertyKey (Optional) The property key to decorate.
             * @param attributes (Optional) The property descriptor for the target key.
             * @remarks Decorators are applied in reverse order.
             * @example
             *
             *     class Example {
             *         // property declarations are not part of ES6, though they are valid in TypeScript:
             *         // static staticProperty;
             *         // property;
             *
             *         constructor(p) { }
             *         static staticMethod(p) { }
             *         method(p) { }
             *     }
             *
             *     // constructor
             *     Example = Reflect.decorate(decoratorsArray, Example);
             *
             *     // property (on constructor)
             *     Reflect.decorate(decoratorsArray, Example, "staticProperty");
             *
             *     // property (on prototype)
             *     Reflect.decorate(decoratorsArray, Example.prototype, "property");
             *
             *     // method (on constructor)
             *     Object.defineProperty(Example, "staticMethod",
             *         Reflect.decorate(decoratorsArray, Example, "staticMethod",
             *             Object.getOwnPropertyDescriptor(Example, "staticMethod")));
             *
             *     // method (on prototype)
             *     Object.defineProperty(Example.prototype, "method",
             *         Reflect.decorate(decoratorsArray, Example.prototype, "method",
             *             Object.getOwnPropertyDescriptor(Example.prototype, "method")));
             *
             */
            function decorate(decorators, target, propertyKey, attributes) {
                if (!IsUndefined(propertyKey)) {
                    if (!IsArray(decorators))
                        throw new TypeError();
                    if (!IsObject(target))
                        throw new TypeError();
                    if (!IsObject(attributes) && !IsUndefined(attributes) && !IsNull(attributes))
                        throw new TypeError();
                    if (IsNull(attributes))
                        attributes = undefined;
                    propertyKey = ToPropertyKey(propertyKey);
                    return DecorateProperty(decorators, target, propertyKey, attributes);
                }
                else {
                    if (!IsArray(decorators))
                        throw new TypeError();
                    if (!IsConstructor(target))
                        throw new TypeError();
                    return DecorateConstructor(decorators, target);
                }
            }
            exporter("decorate", decorate);
            // 4.1.2 Reflect.metadata(metadataKey, metadataValue)
            // https://rbuckton.github.io/reflect-metadata/#reflect.metadata
            /**
             * A default metadata decorator factory that can be used on a class, class member, or parameter.
             * @param metadataKey The key for the metadata entry.
             * @param metadataValue The value for the metadata entry.
             * @returns A decorator function.
             * @remarks
             * If `metadataKey` is already defined for the target and target key, the
             * metadataValue for that key will be overwritten.
             * @example
             *
             *     // constructor
             *     @Reflect.metadata(key, value)
             *     class Example {
             *     }
             *
             *     // property (on constructor, TypeScript only)
             *     class Example {
             *         @Reflect.metadata(key, value)
             *         static staticProperty;
             *     }
             *
             *     // property (on prototype, TypeScript only)
             *     class Example {
             *         @Reflect.metadata(key, value)
             *         property;
             *     }
             *
             *     // method (on constructor)
             *     class Example {
             *         @Reflect.metadata(key, value)
             *         static staticMethod() { }
             *     }
             *
             *     // method (on prototype)
             *     class Example {
             *         @Reflect.metadata(key, value)
             *         method() { }
             *     }
             *
             */
            function metadata(metadataKey, metadataValue) {
                function decorator(target, propertyKey) {
                    if (!IsObject(target))
                        throw new TypeError();
                    if (!IsUndefined(propertyKey) && !IsPropertyKey(propertyKey))
                        throw new TypeError();
                    OrdinaryDefineOwnMetadata(metadataKey, metadataValue, target, propertyKey);
                }
                return decorator;
            }
            exporter("metadata", metadata);
            /**
             * Define a unique metadata entry on the target.
             * @param metadataKey A key used to store and retrieve metadata.
             * @param metadataValue A value that contains attached metadata.
             * @param target The target object on which to define metadata.
             * @param propertyKey (Optional) The property key for the target.
             * @example
             *
             *     class Example {
             *         // property declarations are not part of ES6, though they are valid in TypeScript:
             *         // static staticProperty;
             *         // property;
             *
             *         constructor(p) { }
             *         static staticMethod(p) { }
             *         method(p) { }
             *     }
             *
             *     // constructor
             *     Reflect.defineMetadata("custom:annotation", options, Example);
             *
             *     // property (on constructor)
             *     Reflect.defineMetadata("custom:annotation", options, Example, "staticProperty");
             *
             *     // property (on prototype)
             *     Reflect.defineMetadata("custom:annotation", options, Example.prototype, "property");
             *
             *     // method (on constructor)
             *     Reflect.defineMetadata("custom:annotation", options, Example, "staticMethod");
             *
             *     // method (on prototype)
             *     Reflect.defineMetadata("custom:annotation", options, Example.prototype, "method");
             *
             *     // decorator factory as metadata-producing annotation.
             *     function MyAnnotation(options): Decorator {
             *         return (target, key?) => Reflect.defineMetadata("custom:annotation", options, target, key);
             *     }
             *
             */
            function defineMetadata(metadataKey, metadataValue, target, propertyKey) {
                if (!IsObject(target))
                    throw new TypeError();
                if (!IsUndefined(propertyKey))
                    propertyKey = ToPropertyKey(propertyKey);
                return OrdinaryDefineOwnMetadata(metadataKey, metadataValue, target, propertyKey);
            }
            exporter("defineMetadata", defineMetadata);
            /**
             * Gets a value indicating whether the target object or its prototype chain has the provided metadata key defined.
             * @param metadataKey A key used to store and retrieve metadata.
             * @param target The target object on which the metadata is defined.
             * @param propertyKey (Optional) The property key for the target.
             * @returns `true` if the metadata key was defined on the target object or its prototype chain; otherwise, `false`.
             * @example
             *
             *     class Example {
             *         // property declarations are not part of ES6, though they are valid in TypeScript:
             *         // static staticProperty;
             *         // property;
             *
             *         constructor(p) { }
             *         static staticMethod(p) { }
             *         method(p) { }
             *     }
             *
             *     // constructor
             *     result = Reflect.hasMetadata("custom:annotation", Example);
             *
             *     // property (on constructor)
             *     result = Reflect.hasMetadata("custom:annotation", Example, "staticProperty");
             *
             *     // property (on prototype)
             *     result = Reflect.hasMetadata("custom:annotation", Example.prototype, "property");
             *
             *     // method (on constructor)
             *     result = Reflect.hasMetadata("custom:annotation", Example, "staticMethod");
             *
             *     // method (on prototype)
             *     result = Reflect.hasMetadata("custom:annotation", Example.prototype, "method");
             *
             */
            function hasMetadata(metadataKey, target, propertyKey) {
                if (!IsObject(target))
                    throw new TypeError();
                if (!IsUndefined(propertyKey))
                    propertyKey = ToPropertyKey(propertyKey);
                return OrdinaryHasMetadata(metadataKey, target, propertyKey);
            }
            exporter("hasMetadata", hasMetadata);
            /**
             * Gets a value indicating whether the target object has the provided metadata key defined.
             * @param metadataKey A key used to store and retrieve metadata.
             * @param target The target object on which the metadata is defined.
             * @param propertyKey (Optional) The property key for the target.
             * @returns `true` if the metadata key was defined on the target object; otherwise, `false`.
             * @example
             *
             *     class Example {
             *         // property declarations are not part of ES6, though they are valid in TypeScript:
             *         // static staticProperty;
             *         // property;
             *
             *         constructor(p) { }
             *         static staticMethod(p) { }
             *         method(p) { }
             *     }
             *
             *     // constructor
             *     result = Reflect.hasOwnMetadata("custom:annotation", Example);
             *
             *     // property (on constructor)
             *     result = Reflect.hasOwnMetadata("custom:annotation", Example, "staticProperty");
             *
             *     // property (on prototype)
             *     result = Reflect.hasOwnMetadata("custom:annotation", Example.prototype, "property");
             *
             *     // method (on constructor)
             *     result = Reflect.hasOwnMetadata("custom:annotation", Example, "staticMethod");
             *
             *     // method (on prototype)
             *     result = Reflect.hasOwnMetadata("custom:annotation", Example.prototype, "method");
             *
             */
            function hasOwnMetadata(metadataKey, target, propertyKey) {
                if (!IsObject(target))
                    throw new TypeError();
                if (!IsUndefined(propertyKey))
                    propertyKey = ToPropertyKey(propertyKey);
                return OrdinaryHasOwnMetadata(metadataKey, target, propertyKey);
            }
            exporter("hasOwnMetadata", hasOwnMetadata);
            /**
             * Gets the metadata value for the provided metadata key on the target object or its prototype chain.
             * @param metadataKey A key used to store and retrieve metadata.
             * @param target The target object on which the metadata is defined.
             * @param propertyKey (Optional) The property key for the target.
             * @returns The metadata value for the metadata key if found; otherwise, `undefined`.
             * @example
             *
             *     class Example {
             *         // property declarations are not part of ES6, though they are valid in TypeScript:
             *         // static staticProperty;
             *         // property;
             *
             *         constructor(p) { }
             *         static staticMethod(p) { }
             *         method(p) { }
             *     }
             *
             *     // constructor
             *     result = Reflect.getMetadata("custom:annotation", Example);
             *
             *     // property (on constructor)
             *     result = Reflect.getMetadata("custom:annotation", Example, "staticProperty");
             *
             *     // property (on prototype)
             *     result = Reflect.getMetadata("custom:annotation", Example.prototype, "property");
             *
             *     // method (on constructor)
             *     result = Reflect.getMetadata("custom:annotation", Example, "staticMethod");
             *
             *     // method (on prototype)
             *     result = Reflect.getMetadata("custom:annotation", Example.prototype, "method");
             *
             */
            function getMetadata(metadataKey, target, propertyKey) {
                if (!IsObject(target))
                    throw new TypeError();
                if (!IsUndefined(propertyKey))
                    propertyKey = ToPropertyKey(propertyKey);
                return OrdinaryGetMetadata(metadataKey, target, propertyKey);
            }
            exporter("getMetadata", getMetadata);
            /**
             * Gets the metadata value for the provided metadata key on the target object.
             * @param metadataKey A key used to store and retrieve metadata.
             * @param target The target object on which the metadata is defined.
             * @param propertyKey (Optional) The property key for the target.
             * @returns The metadata value for the metadata key if found; otherwise, `undefined`.
             * @example
             *
             *     class Example {
             *         // property declarations are not part of ES6, though they are valid in TypeScript:
             *         // static staticProperty;
             *         // property;
             *
             *         constructor(p) { }
             *         static staticMethod(p) { }
             *         method(p) { }
             *     }
             *
             *     // constructor
             *     result = Reflect.getOwnMetadata("custom:annotation", Example);
             *
             *     // property (on constructor)
             *     result = Reflect.getOwnMetadata("custom:annotation", Example, "staticProperty");
             *
             *     // property (on prototype)
             *     result = Reflect.getOwnMetadata("custom:annotation", Example.prototype, "property");
             *
             *     // method (on constructor)
             *     result = Reflect.getOwnMetadata("custom:annotation", Example, "staticMethod");
             *
             *     // method (on prototype)
             *     result = Reflect.getOwnMetadata("custom:annotation", Example.prototype, "method");
             *
             */
            function getOwnMetadata(metadataKey, target, propertyKey) {
                if (!IsObject(target))
                    throw new TypeError();
                if (!IsUndefined(propertyKey))
                    propertyKey = ToPropertyKey(propertyKey);
                return OrdinaryGetOwnMetadata(metadataKey, target, propertyKey);
            }
            exporter("getOwnMetadata", getOwnMetadata);
            /**
             * Gets the metadata keys defined on the target object or its prototype chain.
             * @param target The target object on which the metadata is defined.
             * @param propertyKey (Optional) The property key for the target.
             * @returns An array of unique metadata keys.
             * @example
             *
             *     class Example {
             *         // property declarations are not part of ES6, though they are valid in TypeScript:
             *         // static staticProperty;
             *         // property;
             *
             *         constructor(p) { }
             *         static staticMethod(p) { }
             *         method(p) { }
             *     }
             *
             *     // constructor
             *     result = Reflect.getMetadataKeys(Example);
             *
             *     // property (on constructor)
             *     result = Reflect.getMetadataKeys(Example, "staticProperty");
             *
             *     // property (on prototype)
             *     result = Reflect.getMetadataKeys(Example.prototype, "property");
             *
             *     // method (on constructor)
             *     result = Reflect.getMetadataKeys(Example, "staticMethod");
             *
             *     // method (on prototype)
             *     result = Reflect.getMetadataKeys(Example.prototype, "method");
             *
             */
            function getMetadataKeys(target, propertyKey) {
                if (!IsObject(target))
                    throw new TypeError();
                if (!IsUndefined(propertyKey))
                    propertyKey = ToPropertyKey(propertyKey);
                return OrdinaryMetadataKeys(target, propertyKey);
            }
            exporter("getMetadataKeys", getMetadataKeys);
            /**
             * Gets the unique metadata keys defined on the target object.
             * @param target The target object on which the metadata is defined.
             * @param propertyKey (Optional) The property key for the target.
             * @returns An array of unique metadata keys.
             * @example
             *
             *     class Example {
             *         // property declarations are not part of ES6, though they are valid in TypeScript:
             *         // static staticProperty;
             *         // property;
             *
             *         constructor(p) { }
             *         static staticMethod(p) { }
             *         method(p) { }
             *     }
             *
             *     // constructor
             *     result = Reflect.getOwnMetadataKeys(Example);
             *
             *     // property (on constructor)
             *     result = Reflect.getOwnMetadataKeys(Example, "staticProperty");
             *
             *     // property (on prototype)
             *     result = Reflect.getOwnMetadataKeys(Example.prototype, "property");
             *
             *     // method (on constructor)
             *     result = Reflect.getOwnMetadataKeys(Example, "staticMethod");
             *
             *     // method (on prototype)
             *     result = Reflect.getOwnMetadataKeys(Example.prototype, "method");
             *
             */
            function getOwnMetadataKeys(target, propertyKey) {
                if (!IsObject(target))
                    throw new TypeError();
                if (!IsUndefined(propertyKey))
                    propertyKey = ToPropertyKey(propertyKey);
                return OrdinaryOwnMetadataKeys(target, propertyKey);
            }
            exporter("getOwnMetadataKeys", getOwnMetadataKeys);
            /**
             * Deletes the metadata entry from the target object with the provided key.
             * @param metadataKey A key used to store and retrieve metadata.
             * @param target The target object on which the metadata is defined.
             * @param propertyKey (Optional) The property key for the target.
             * @returns `true` if the metadata entry was found and deleted; otherwise, false.
             * @example
             *
             *     class Example {
             *         // property declarations are not part of ES6, though they are valid in TypeScript:
             *         // static staticProperty;
             *         // property;
             *
             *         constructor(p) { }
             *         static staticMethod(p) { }
             *         method(p) { }
             *     }
             *
             *     // constructor
             *     result = Reflect.deleteMetadata("custom:annotation", Example);
             *
             *     // property (on constructor)
             *     result = Reflect.deleteMetadata("custom:annotation", Example, "staticProperty");
             *
             *     // property (on prototype)
             *     result = Reflect.deleteMetadata("custom:annotation", Example.prototype, "property");
             *
             *     // method (on constructor)
             *     result = Reflect.deleteMetadata("custom:annotation", Example, "staticMethod");
             *
             *     // method (on prototype)
             *     result = Reflect.deleteMetadata("custom:annotation", Example.prototype, "method");
             *
             */
            function deleteMetadata(metadataKey, target, propertyKey) {
                if (!IsObject(target))
                    throw new TypeError();
                if (!IsUndefined(propertyKey))
                    propertyKey = ToPropertyKey(propertyKey);
                var metadataMap = GetOrCreateMetadataMap(target, propertyKey, /*Create*/ false);
                if (IsUndefined(metadataMap))
                    return false;
                if (!metadataMap.delete(metadataKey))
                    return false;
                if (metadataMap.size > 0)
                    return true;
                var targetMetadata = Metadata.get(target);
                targetMetadata.delete(propertyKey);
                if (targetMetadata.size > 0)
                    return true;
                Metadata.delete(target);
                return true;
            }
            exporter("deleteMetadata", deleteMetadata);
            function DecorateConstructor(decorators, target) {
                for (var i = decorators.length - 1; i >= 0; --i) {
                    var decorator = decorators[i];
                    var decorated = decorator(target);
                    if (!IsUndefined(decorated) && !IsNull(decorated)) {
                        if (!IsConstructor(decorated))
                            throw new TypeError();
                        target = decorated;
                    }
                }
                return target;
            }
            function DecorateProperty(decorators, target, propertyKey, descriptor) {
                for (var i = decorators.length - 1; i >= 0; --i) {
                    var decorator = decorators[i];
                    var decorated = decorator(target, propertyKey, descriptor);
                    if (!IsUndefined(decorated) && !IsNull(decorated)) {
                        if (!IsObject(decorated))
                            throw new TypeError();
                        descriptor = decorated;
                    }
                }
                return descriptor;
            }
            function GetOrCreateMetadataMap(O, P, Create) {
                var targetMetadata = Metadata.get(O);
                if (IsUndefined(targetMetadata)) {
                    if (!Create)
                        return undefined;
                    targetMetadata = new _Map();
                    Metadata.set(O, targetMetadata);
                }
                var metadataMap = targetMetadata.get(P);
                if (IsUndefined(metadataMap)) {
                    if (!Create)
                        return undefined;
                    metadataMap = new _Map();
                    targetMetadata.set(P, metadataMap);
                }
                return metadataMap;
            }
            // 3.1.1.1 OrdinaryHasMetadata(MetadataKey, O, P)
            // https://rbuckton.github.io/reflect-metadata/#ordinaryhasmetadata
            function OrdinaryHasMetadata(MetadataKey, O, P) {
                var hasOwn = OrdinaryHasOwnMetadata(MetadataKey, O, P);
                if (hasOwn)
                    return true;
                var parent = OrdinaryGetPrototypeOf(O);
                if (!IsNull(parent))
                    return OrdinaryHasMetadata(MetadataKey, parent, P);
                return false;
            }
            // 3.1.2.1 OrdinaryHasOwnMetadata(MetadataKey, O, P)
            // https://rbuckton.github.io/reflect-metadata/#ordinaryhasownmetadata
            function OrdinaryHasOwnMetadata(MetadataKey, O, P) {
                var metadataMap = GetOrCreateMetadataMap(O, P, /*Create*/ false);
                if (IsUndefined(metadataMap))
                    return false;
                return ToBoolean(metadataMap.has(MetadataKey));
            }
            // 3.1.3.1 OrdinaryGetMetadata(MetadataKey, O, P)
            // https://rbuckton.github.io/reflect-metadata/#ordinarygetmetadata
            function OrdinaryGetMetadata(MetadataKey, O, P) {
                var hasOwn = OrdinaryHasOwnMetadata(MetadataKey, O, P);
                if (hasOwn)
                    return OrdinaryGetOwnMetadata(MetadataKey, O, P);
                var parent = OrdinaryGetPrototypeOf(O);
                if (!IsNull(parent))
                    return OrdinaryGetMetadata(MetadataKey, parent, P);
                return undefined;
            }
            // 3.1.4.1 OrdinaryGetOwnMetadata(MetadataKey, O, P)
            // https://rbuckton.github.io/reflect-metadata/#ordinarygetownmetadata
            function OrdinaryGetOwnMetadata(MetadataKey, O, P) {
                var metadataMap = GetOrCreateMetadataMap(O, P, /*Create*/ false);
                if (IsUndefined(metadataMap))
                    return undefined;
                return metadataMap.get(MetadataKey);
            }
            // 3.1.5.1 OrdinaryDefineOwnMetadata(MetadataKey, MetadataValue, O, P)
            // https://rbuckton.github.io/reflect-metadata/#ordinarydefineownmetadata
            function OrdinaryDefineOwnMetadata(MetadataKey, MetadataValue, O, P) {
                var metadataMap = GetOrCreateMetadataMap(O, P, /*Create*/ true);
                metadataMap.set(MetadataKey, MetadataValue);
            }
            // 3.1.6.1 OrdinaryMetadataKeys(O, P)
            // https://rbuckton.github.io/reflect-metadata/#ordinarymetadatakeys
            function OrdinaryMetadataKeys(O, P) {
                var ownKeys = OrdinaryOwnMetadataKeys(O, P);
                var parent = OrdinaryGetPrototypeOf(O);
                if (parent === null)
                    return ownKeys;
                var parentKeys = OrdinaryMetadataKeys(parent, P);
                if (parentKeys.length <= 0)
                    return ownKeys;
                if (ownKeys.length <= 0)
                    return parentKeys;
                var set = new _Set();
                var keys = [];
                for (var _i = 0, ownKeys_1 = ownKeys; _i < ownKeys_1.length; _i++) {
                    var key = ownKeys_1[_i];
                    var hasKey = set.has(key);
                    if (!hasKey) {
                        set.add(key);
                        keys.push(key);
                    }
                }
                for (var _a = 0, parentKeys_1 = parentKeys; _a < parentKeys_1.length; _a++) {
                    var key = parentKeys_1[_a];
                    var hasKey = set.has(key);
                    if (!hasKey) {
                        set.add(key);
                        keys.push(key);
                    }
                }
                return keys;
            }
            // 3.1.7.1 OrdinaryOwnMetadataKeys(O, P)
            // https://rbuckton.github.io/reflect-metadata/#ordinaryownmetadatakeys
            function OrdinaryOwnMetadataKeys(O, P) {
                var keys = [];
                var metadataMap = GetOrCreateMetadataMap(O, P, /*Create*/ false);
                if (IsUndefined(metadataMap))
                    return keys;
                var keysObj = metadataMap.keys();
                var iterator = GetIterator(keysObj);
                var k = 0;
                while (true) {
                    var next = IteratorStep(iterator);
                    if (!next) {
                        keys.length = k;
                        return keys;
                    }
                    var nextValue = IteratorValue(next);
                    try {
                        keys[k] = nextValue;
                    }
                    catch (e) {
                        try {
                            IteratorClose(iterator);
                        }
                        finally {
                            throw e;
                        }
                    }
                    k++;
                }
            }
            // 6 ECMAScript Data Typ0es and Values
            // https://tc39.github.io/ecma262/#sec-ecmascript-data-types-and-values
            function Type(x) {
                if (x === null)
                    return 1 /* Null */;
                switch (typeof x) {
                    case "undefined": return 0 /* Undefined */;
                    case "boolean": return 2 /* Boolean */;
                    case "string": return 3 /* String */;
                    case "symbol": return 4 /* Symbol */;
                    case "number": return 5 /* Number */;
                    case "object": return x === null ? 1 /* Null */ : 6 /* Object */;
                    default: return 6 /* Object */;
                }
            }
            // 6.1.1 The Undefined Type
            // https://tc39.github.io/ecma262/#sec-ecmascript-language-types-undefined-type
            function IsUndefined(x) {
                return x === undefined;
            }
            // 6.1.2 The Null Type
            // https://tc39.github.io/ecma262/#sec-ecmascript-language-types-null-type
            function IsNull(x) {
                return x === null;
            }
            // 6.1.5 The Symbol Type
            // https://tc39.github.io/ecma262/#sec-ecmascript-language-types-symbol-type
            function IsSymbol(x) {
                return typeof x === "symbol";
            }
            // 6.1.7 The Object Type
            // https://tc39.github.io/ecma262/#sec-object-type
            function IsObject(x) {
                return typeof x === "object" ? x !== null : typeof x === "function";
            }
            // 7.1 Type Conversion
            // https://tc39.github.io/ecma262/#sec-type-conversion
            // 7.1.1 ToPrimitive(input [, PreferredType])
            // https://tc39.github.io/ecma262/#sec-toprimitive
            function ToPrimitive(input, PreferredType) {
                switch (Type(input)) {
                    case 0 /* Undefined */: return input;
                    case 1 /* Null */: return input;
                    case 2 /* Boolean */: return input;
                    case 3 /* String */: return input;
                    case 4 /* Symbol */: return input;
                    case 5 /* Number */: return input;
                }
                var hint = PreferredType === 3 /* String */ ? "string" : PreferredType === 5 /* Number */ ? "number" : "default";
                var exoticToPrim = GetMethod(input, toPrimitiveSymbol);
                if (exoticToPrim !== undefined) {
                    var result = exoticToPrim.call(input, hint);
                    if (IsObject(result))
                        throw new TypeError();
                    return result;
                }
                return OrdinaryToPrimitive(input, hint === "default" ? "number" : hint);
            }
            // 7.1.1.1 OrdinaryToPrimitive(O, hint)
            // https://tc39.github.io/ecma262/#sec-ordinarytoprimitive
            function OrdinaryToPrimitive(O, hint) {
                if (hint === "string") {
                    var toString_1 = O.toString;
                    if (IsCallable(toString_1)) {
                        var result = toString_1.call(O);
                        if (!IsObject(result))
                            return result;
                    }
                    var valueOf = O.valueOf;
                    if (IsCallable(valueOf)) {
                        var result = valueOf.call(O);
                        if (!IsObject(result))
                            return result;
                    }
                }
                else {
                    var valueOf = O.valueOf;
                    if (IsCallable(valueOf)) {
                        var result = valueOf.call(O);
                        if (!IsObject(result))
                            return result;
                    }
                    var toString_2 = O.toString;
                    if (IsCallable(toString_2)) {
                        var result = toString_2.call(O);
                        if (!IsObject(result))
                            return result;
                    }
                }
                throw new TypeError();
            }
            // 7.1.2 ToBoolean(argument)
            // https://tc39.github.io/ecma262/2016/#sec-toboolean
            function ToBoolean(argument) {
                return !!argument;
            }
            // 7.1.12 ToString(argument)
            // https://tc39.github.io/ecma262/#sec-tostring
            function ToString(argument) {
                return "" + argument;
            }
            // 7.1.14 ToPropertyKey(argument)
            // https://tc39.github.io/ecma262/#sec-topropertykey
            function ToPropertyKey(argument) {
                var key = ToPrimitive(argument, 3 /* String */);
                if (IsSymbol(key))
                    return key;
                return ToString(key);
            }
            // 7.2 Testing and Comparison Operations
            // https://tc39.github.io/ecma262/#sec-testing-and-comparison-operations
            // 7.2.2 IsArray(argument)
            // https://tc39.github.io/ecma262/#sec-isarray
            function IsArray(argument) {
                return Array.isArray
                    ? Array.isArray(argument)
                    : argument instanceof Object
                        ? argument instanceof Array
                        : Object.prototype.toString.call(argument) === "[object Array]";
            }
            // 7.2.3 IsCallable(argument)
            // https://tc39.github.io/ecma262/#sec-iscallable
            function IsCallable(argument) {
                // NOTE: This is an approximation as we cannot check for [[Call]] internal method.
                return typeof argument === "function";
            }
            // 7.2.4 IsConstructor(argument)
            // https://tc39.github.io/ecma262/#sec-isconstructor
            function IsConstructor(argument) {
                // NOTE: This is an approximation as we cannot check for [[Construct]] internal method.
                return typeof argument === "function";
            }
            // 7.2.7 IsPropertyKey(argument)
            // https://tc39.github.io/ecma262/#sec-ispropertykey
            function IsPropertyKey(argument) {
                switch (Type(argument)) {
                    case 3 /* String */: return true;
                    case 4 /* Symbol */: return true;
                    default: return false;
                }
            }
            // 7.3 Operations on Objects
            // https://tc39.github.io/ecma262/#sec-operations-on-objects
            // 7.3.9 GetMethod(V, P)
            // https://tc39.github.io/ecma262/#sec-getmethod
            function GetMethod(V, P) {
                var func = V[P];
                if (func === undefined || func === null)
                    return undefined;
                if (!IsCallable(func))
                    throw new TypeError();
                return func;
            }
            // 7.4 Operations on Iterator Objects
            // https://tc39.github.io/ecma262/#sec-operations-on-iterator-objects
            function GetIterator(obj) {
                var method = GetMethod(obj, iteratorSymbol);
                if (!IsCallable(method))
                    throw new TypeError(); // from Call
                var iterator = method.call(obj);
                if (!IsObject(iterator))
                    throw new TypeError();
                return iterator;
            }
            // 7.4.4 IteratorValue(iterResult)
            // https://tc39.github.io/ecma262/2016/#sec-iteratorvalue
            function IteratorValue(iterResult) {
                return iterResult.value;
            }
            // 7.4.5 IteratorStep(iterator)
            // https://tc39.github.io/ecma262/#sec-iteratorstep
            function IteratorStep(iterator) {
                var result = iterator.next();
                return result.done ? false : result;
            }
            // 7.4.6 IteratorClose(iterator, completion)
            // https://tc39.github.io/ecma262/#sec-iteratorclose
            function IteratorClose(iterator) {
                var f = iterator["return"];
                if (f)
                    f.call(iterator);
            }
            // 9.1 Ordinary Object Internal Methods and Internal Slots
            // https://tc39.github.io/ecma262/#sec-ordinary-object-internal-methods-and-internal-slots
            // 9.1.1.1 OrdinaryGetPrototypeOf(O)
            // https://tc39.github.io/ecma262/#sec-ordinarygetprototypeof
            function OrdinaryGetPrototypeOf(O) {
                var proto = Object.getPrototypeOf(O);
                if (typeof O !== "function" || O === functionPrototype)
                    return proto;
                // TypeScript doesn't set __proto__ in ES5, as it's non-standard.
                // Try to determine the superclass constructor. Compatible implementations
                // must either set __proto__ on a subclass constructor to the superclass constructor,
                // or ensure each class has a valid `constructor` property on its prototype that
                // points back to the constructor.
                // If this is not the same as Function.[[Prototype]], then this is definately inherited.
                // This is the case when in ES6 or when using __proto__ in a compatible browser.
                if (proto !== functionPrototype)
                    return proto;
                // If the super prototype is Object.prototype, null, or undefined, then we cannot determine the heritage.
                var prototype = O.prototype;
                var prototypeProto = prototype && Object.getPrototypeOf(prototype);
                if (prototypeProto == null || prototypeProto === Object.prototype)
                    return proto;
                // If the constructor was not a function, then we cannot determine the heritage.
                var constructor = prototypeProto.constructor;
                if (typeof constructor !== "function")
                    return proto;
                // If we have some kind of self-reference, then we cannot determine the heritage.
                if (constructor === O)
                    return proto;
                // we have a pretty good guess at the heritage.
                return constructor;
            }
            // naive Map shim
            function CreateMapPolyfill() {
                var cacheSentinel = {};
                var arraySentinel = [];
                var MapIterator = /** @class */ (function () {
                    function MapIterator(keys, values, selector) {
                        this._index = 0;
                        this._keys = keys;
                        this._values = values;
                        this._selector = selector;
                    }
                    MapIterator.prototype["@@iterator"] = function () { return this; };
                    MapIterator.prototype[iteratorSymbol] = function () { return this; };
                    MapIterator.prototype.next = function () {
                        var index = this._index;
                        if (index >= 0 && index < this._keys.length) {
                            var result = this._selector(this._keys[index], this._values[index]);
                            if (index + 1 >= this._keys.length) {
                                this._index = -1;
                                this._keys = arraySentinel;
                                this._values = arraySentinel;
                            }
                            else {
                                this._index++;
                            }
                            return { value: result, done: false };
                        }
                        return { value: undefined, done: true };
                    };
                    MapIterator.prototype.throw = function (error) {
                        if (this._index >= 0) {
                            this._index = -1;
                            this._keys = arraySentinel;
                            this._values = arraySentinel;
                        }
                        throw error;
                    };
                    MapIterator.prototype.return = function (value) {
                        if (this._index >= 0) {
                            this._index = -1;
                            this._keys = arraySentinel;
                            this._values = arraySentinel;
                        }
                        return { value: value, done: true };
                    };
                    return MapIterator;
                }());
                return /** @class */ (function () {
                    function Map() {
                        this._keys = [];
                        this._values = [];
                        this._cacheKey = cacheSentinel;
                        this._cacheIndex = -2;
                    }
                    Object.defineProperty(Map.prototype, "size", {
                        get: function () { return this._keys.length; },
                        enumerable: true,
                        configurable: true
                    });
                    Map.prototype.has = function (key) { return this._find(key, /*insert*/ false) >= 0; };
                    Map.prototype.get = function (key) {
                        var index = this._find(key, /*insert*/ false);
                        return index >= 0 ? this._values[index] : undefined;
                    };
                    Map.prototype.set = function (key, value) {
                        var index = this._find(key, /*insert*/ true);
                        this._values[index] = value;
                        return this;
                    };
                    Map.prototype.delete = function (key) {
                        var index = this._find(key, /*insert*/ false);
                        if (index >= 0) {
                            var size = this._keys.length;
                            for (var i = index + 1; i < size; i++) {
                                this._keys[i - 1] = this._keys[i];
                                this._values[i - 1] = this._values[i];
                            }
                            this._keys.length--;
                            this._values.length--;
                            if (key === this._cacheKey) {
                                this._cacheKey = cacheSentinel;
                                this._cacheIndex = -2;
                            }
                            return true;
                        }
                        return false;
                    };
                    Map.prototype.clear = function () {
                        this._keys.length = 0;
                        this._values.length = 0;
                        this._cacheKey = cacheSentinel;
                        this._cacheIndex = -2;
                    };
                    Map.prototype.keys = function () { return new MapIterator(this._keys, this._values, getKey); };
                    Map.prototype.values = function () { return new MapIterator(this._keys, this._values, getValue); };
                    Map.prototype.entries = function () { return new MapIterator(this._keys, this._values, getEntry); };
                    Map.prototype["@@iterator"] = function () { return this.entries(); };
                    Map.prototype[iteratorSymbol] = function () { return this.entries(); };
                    Map.prototype._find = function (key, insert) {
                        if (this._cacheKey !== key) {
                            this._cacheIndex = this._keys.indexOf(this._cacheKey = key);
                        }
                        if (this._cacheIndex < 0 && insert) {
                            this._cacheIndex = this._keys.length;
                            this._keys.push(key);
                            this._values.push(undefined);
                        }
                        return this._cacheIndex;
                    };
                    return Map;
                }());
                function getKey(key, _) {
                    return key;
                }
                function getValue(_, value) {
                    return value;
                }
                function getEntry(key, value) {
                    return [key, value];
                }
            }
            // naive Set shim
            function CreateSetPolyfill() {
                return /** @class */ (function () {
                    function Set() {
                        this._map = new _Map();
                    }
                    Object.defineProperty(Set.prototype, "size", {
                        get: function () { return this._map.size; },
                        enumerable: true,
                        configurable: true
                    });
                    Set.prototype.has = function (value) { return this._map.has(value); };
                    Set.prototype.add = function (value) { return this._map.set(value, value), this; };
                    Set.prototype.delete = function (value) { return this._map.delete(value); };
                    Set.prototype.clear = function () { this._map.clear(); };
                    Set.prototype.keys = function () { return this._map.keys(); };
                    Set.prototype.values = function () { return this._map.values(); };
                    Set.prototype.entries = function () { return this._map.entries(); };
                    Set.prototype["@@iterator"] = function () { return this.keys(); };
                    Set.prototype[iteratorSymbol] = function () { return this.keys(); };
                    return Set;
                }());
            }
            // naive WeakMap shim
            function CreateWeakMapPolyfill() {
                var UUID_SIZE = 16;
                var keys = HashMap.create();
                var rootKey = CreateUniqueKey();
                return /** @class */ (function () {
                    function WeakMap() {
                        this._key = CreateUniqueKey();
                    }
                    WeakMap.prototype.has = function (target) {
                        var table = GetOrCreateWeakMapTable(target, /*create*/ false);
                        return table !== undefined ? HashMap.has(table, this._key) : false;
                    };
                    WeakMap.prototype.get = function (target) {
                        var table = GetOrCreateWeakMapTable(target, /*create*/ false);
                        return table !== undefined ? HashMap.get(table, this._key) : undefined;
                    };
                    WeakMap.prototype.set = function (target, value) {
                        var table = GetOrCreateWeakMapTable(target, /*create*/ true);
                        table[this._key] = value;
                        return this;
                    };
                    WeakMap.prototype.delete = function (target) {
                        var table = GetOrCreateWeakMapTable(target, /*create*/ false);
                        return table !== undefined ? delete table[this._key] : false;
                    };
                    WeakMap.prototype.clear = function () {
                        // NOTE: not a real clear, just makes the previous data unreachable
                        this._key = CreateUniqueKey();
                    };
                    return WeakMap;
                }());
                function CreateUniqueKey() {
                    var key;
                    do
                        key = "@@WeakMap@@" + CreateUUID();
                    while (HashMap.has(keys, key));
                    keys[key] = true;
                    return key;
                }
                function GetOrCreateWeakMapTable(target, create) {
                    if (!hasOwn.call(target, rootKey)) {
                        if (!create)
                            return undefined;
                        Object.defineProperty(target, rootKey, { value: HashMap.create() });
                    }
                    return target[rootKey];
                }
                function FillRandomBytes(buffer, size) {
                    for (var i = 0; i < size; ++i)
                        buffer[i] = Math.random() * 0xff | 0;
                    return buffer;
                }
                function GenRandomBytes(size) {
                    if (typeof Uint8Array === "function") {
                        if (typeof crypto !== "undefined")
                            return crypto.getRandomValues(new Uint8Array(size));
                        if (typeof msCrypto !== "undefined")
                            return msCrypto.getRandomValues(new Uint8Array(size));
                        return FillRandomBytes(new Uint8Array(size), size);
                    }
                    return FillRandomBytes(new Array(size), size);
                }
                function CreateUUID() {
                    var data = GenRandomBytes(UUID_SIZE);
                    // mark as random - RFC 4122 § 4.4
                    data[6] = data[6] & 0x4f | 0x40;
                    data[8] = data[8] & 0xbf | 0x80;
                    var result = "";
                    for (var offset = 0; offset < UUID_SIZE; ++offset) {
                        var byte = data[offset];
                        if (offset === 4 || offset === 6 || offset === 8)
                            result += "-";
                        if (byte < 16)
                            result += "0";
                        result += byte.toString(16).toLowerCase();
                    }
                    return result;
                }
            }
            // uses a heuristic used by v8 and chakra to force an object into dictionary mode.
            function MakeDictionary(obj) {
                obj.__ = undefined;
                delete obj.__;
                return obj;
            }
        });
    })(Reflect$1 || (Reflect$1 = {}));

    var i=function(){function e(){}return e.getBaseClass=function(e){return e?Reflect.getPrototypeOf(e):void 0},e.getJsonPropertiesMetadata=function(t,i){if(t){var r=""+e.apiMap+(i||t.constructor.name);return Reflect.getMetadata(r,t)}},e.getParamTypes=function(t){return t?Reflect.getMetadata(e.designParamTypes,t):void 0},e.getJsonObjectMetadata=function(t){return t?Reflect.getMetadata(e.apiMapJsonObject,t):void 0},e.getType=function(t,i){return t?Reflect.getMetadata(e.designType,t,i):void 0},e.isJsonObject=function(t){return !!t&&Reflect.hasOwnMetadata(e.apiMapJsonObject,t)},e.setJsonPropertiesMetadata=function(t,i){if(i){var r=""+e.apiMap+i.constructor.name;Reflect.defineMetadata(r,t,i);}},e.setJsonObject=function(t,i){i&&Reflect.defineMetadata(e.apiMapJsonObject,t,i);},e.setType=function(t,i,r){i&&t&&Reflect.defineMetadata(e.designType,t,i,r);},e.apiMap="api:map:",e.apiMapJsonObject=e.apiMap+"jsonObject",e.designType="design:type",e.designParamTypes="design:paramtypes",e}(),r=function(e){return "string"==typeof e},n=function(e){return null!==e&&"object"==typeof e&&!o(e)},o=function(e){return Array.isArray(e)},a=function(e){return "[object Date]"===toString.call(e)},s=function(e){return [null,void 0].includes(e)},l=function(e){return i.isJsonObject(e)},u=function(e){try{var t=JSON.parse(e);return "object"==typeof t?t:e}catch(t){return e}},c=function(){this.errorCallback=f,this.nullishPolicy={undefined:"remove",null:"allow"};},f=function(e){console.error(e);},d=function(){function p(e){this.options=new c,this.options=__assign(__assign({},this.options),e);}return p.prototype.deserialize=function(e,t){return r(e)&&(e=u(e)),o(e)?this.deserializeObjectArray(e,t):n(e)?this.deserializeObject(e,t):void this.error("Fail to deserialize: value is not an Array nor an Object.\nReceived: "+JSON.stringify(e)+".")},p.prototype.deserializeObject=function(e,t){var i=this;if(null===e)return "disallow"===this.options.nullishPolicy.null&&this.error("Fail to deserialize: null is not assignable to type Object."),null;if(void 0!==e){if(r(e)&&(e=u(e)),n(e)){var o=function(e){if("function"!=typeof e)return !1;try{Reflect.construct(String,[],e);}catch(e){return !1}return !0}(t)?new t({}):t,a=this.getJsonPropertiesMetadata(o);return a?(Object.keys(a).forEach((function(t){var r=a[t],n=i.deserializeProperty(o,t,e,r);if(r.required&&s(n)){var l=o.constructor.name;i.error("Property '"+t+"' is required in "+l+" "+JSON.stringify(e)+".");}i.isAllowedProperty(n)&&(o[t]=n);})),o):o}this.error("Fail to deserialize: type '"+typeof e+"' is not assignable to type 'Object'.\nReceived: "+JSON.stringify(e));}else "disallow"===this.options.nullishPolicy.undefined&&this.error("Fail to deserialize: undefined is not assignable to type Object.");},p.prototype.deserializeObjectArray=function(e,t){var i=this;if(null===e)return "disallow"===this.options.nullishPolicy.null&&this.error("Fail to deserialize: null is not assignable to type Array."),null;if(void 0!==e){if(r(e)&&(e=u(e)),o(e))return e.reduce((function(e,r){var n=i.deserializeObject(r,t);return (!s(n)||null===n&&"remove"!==i.options.nullishPolicy.null||void 0===n&&"remove"!==i.options.nullishPolicy.undefined)&&e.push(n),e}),[]);this.error("Fail to deserialize: type '"+typeof e+"' is not assignable to type 'Array'.\nReceived: "+JSON.stringify(e));}else "disallow"===this.options.nullishPolicy.undefined&&this.error("Fail to deserialize: undefined is not assignable to type Array.");},p.prototype.serialize=function(e){return o(e)?this.serializeObjectArray(e):n(e)?this.serializeObject(e):void this.error("Fail to serialize: value is not an Array nor an Object.\nReceived: "+JSON.stringify(e)+".")},p.prototype.serializeObject=function(e){var t=this;if(null===e)return "disallow"===this.options.nullishPolicy.null&&this.error("Fail to serialize: null is not assignable to type Object."),null;if(void 0!==e){if(!n(e))return e;var i=this.getJsonPropertiesMetadata(e);if(!i)return e;var r={},a=Object.keys(e);return Object.keys(i).forEach((function(n){if(a.includes(n)){var s=i[n],l=void 0;s.beforeSerialize&&(l=e[n],e[n]=s.beforeSerialize(e[n],e));var u=t.serializeProperty(e,n,s);if(s.afterSerialize&&(u=s.afterSerialize(u,e)),e[n]=l||e[n],o(s.name))s.name.forEach((function(e){t.isAllowedProperty(u[e])&&(r[e]=u[e]);}));else if(t.isAllowedProperty(u))if(s.isNameOverridden||void 0===t.options.formatPropertyName)r[s.name]=u;else {var c=t.options.formatPropertyName(s.name);r[c]=u;}}else "remove"!==t.options.nullishPolicy.undefined&&(r[n]=void 0);})),r}"disallow"===this.options.nullishPolicy.undefined&&this.error("Fail to serialize: undefined is not assignable to type Object.");},p.prototype.serializeObjectArray=function(e){var t=this;if(null===e)return "disallow"===this.options.nullishPolicy.null&&this.error("Fail to serialize: null is not assignable to type Array."),null;if(void 0!==e){if(o(e))return e.reduce((function(e,i){var r=t.serializeObject(i);return (!s(r)||null===r&&"remove"!==t.options.nullishPolicy.null||void 0===r&&"remove"!==t.options.nullishPolicy.undefined)&&e.push(r),e}),[]);this.error("Fail to serialize: type '"+typeof e+"' is not assignable to type 'Array'.\nReceived: "+JSON.stringify(e)+".");}else "disallow"===this.options.nullishPolicy.undefined&&this.error("Fail to serialize: undefined is not assignable to type Array.");},p.prototype.deserializeProperty=function(e,t,r,n){var o;if(!s(r)){var a=this.getDataSource(r,n,this.options.formatPropertyName);if(s(a))return a;var u,c=i.getType(e,t),p=null===(o=null==c?void 0:c.name)||void 0===o?void 0:o.toLowerCase(),f="array"===p,d="set"===p,y="map"===p,v=n.type||c;n.beforeDeserialize&&(a=n.beforeDeserialize(a,e));var h=n.predicate;return n.isDictionary||y?(u=this.deserializeDictionary(a,v,h),y&&(u=new Map(Object.entries(u)))):f||d?(u=this.deserializeArray(a,v,h),d&&(u=new Set(u))):!l(v)&&!h||h&&!h(a,r)?u=this.deserializePrimitive(a,v.name):(v=n.predicate?n.predicate(a,r):v,u=this.deserializeObject(a,v)),n.afterDeserialize&&(u=n.afterDeserialize(u,e)),u}},p.prototype.deserializePrimitive=function(e,t){if(s(t))return e;if(typeof e===(t=t.toLowerCase()))return e;var i="Fail to deserialize: type '"+typeof e+"' is not assignable to type '"+t+"'.\nReceived: "+JSON.stringify(e);switch(t){case"string":var r=e.toString();return "[object Object]"===r?void this.error(i):r;case"number":return function(e){return "number"==typeof e}(e)?+e:void this.error(i);case"boolean":return void this.error(i);case"date":return function(e){return !a(e)&&!o(e)&&!isNaN(Date.parse(e))}(e)?new Date(e):void this.error(i);default:return e}},p.prototype.deserializeDictionary=function(e,t,i){var r=this;if(n(e)){var o={};return Object.keys(e).forEach((function(n){var a=i?i(e[n],e):void 0;l(t)||a?o[n]=r.deserializeObject(e[n],a||t):o[n]=r.deserializePrimitive(e[n],typeof e[n]);})),o}this.error("Fail to deserialize: type '"+typeof e+"' is not assignable to type 'Dictionary'.\nReceived: "+JSON.stringify(e)+".");},p.prototype.deserializeArray=function(e,t,i){var r=this;if(o(e))return e.reduce((function(n,o){var a;return l(t)||i?(t=i?i(o,e):t,a=r.deserializeObject(o,t)):a=r.deserializePrimitive(o,typeof o),(!s(a)||null===a&&"remove"!==r.options.nullishPolicy.null||void 0===a&&"remove"!==r.options.nullishPolicy.undefined)&&n.push(a),n}),[]);this.error("Fail to deserialize: type '"+typeof e+"' is not assignable to type 'Array'.\nReceived: "+JSON.stringify(e));},p.prototype.error=function(e){this.options.errorCallback&&this.options.errorCallback(e);},p.prototype.getClassesJsonPropertiesMetadata=function(e,t){return e?e.reduce((function(e,r){var n=i.getJsonPropertiesMetadata(t,r);return n&&e.push(n),e}),[]):[]},p.prototype.getDataSource=function(e,t,i){var r=t.name,n=t.isNameOverridden;if(o(r)){var a={};return r.forEach((function(t){return a[t]=e[t]})),a}return !n&&i?(r=i(r),e[r]):e[r]},p.prototype.getJsonPropertiesMetadata=function(t){var r,n=(null!==(r=i.getJsonObjectMetadata(t.constructor))&&void 0!==r?r:{}).baseClassNames,o=i.getJsonPropertiesMetadata(t);if(!(o||n&&n.length))return o;if(n&&n.length){var a=this.getClassesJsonPropertiesMetadata(n,t);return this.mergeJsonPropertiesMetadata.apply(this,__spreadArray(__spreadArray([],a),[o]))}return o},p.prototype.isAllowedProperty=function(e){if(s(e)){if("disallow"===this.options.nullishPolicy[""+e])return this.error("Disallowed "+e+" value detected."),!1;if("remove"===this.options.nullishPolicy[""+e])return !1}return !0},p.prototype.mergeJsonPropertiesMetadata=function(){for(var e=[],i=0;i<arguments.length;i++)e[i]=arguments[i];var r={};return e.forEach((function(e){e&&Object.keys(e).forEach((function(i){r[i]=__assign(__assign({},r[i]),e[i]);}));})),r},p.prototype.serializeDictionary=function(e){var t=this;if(n(e)){var i={};return Object.keys(e).forEach((function(r){i[r]=t.serializeObject(e[r]);})),i}this.error("Fail to serialize: type '"+typeof e+"' is not assignable to type 'Dictionary'.\nReceived: "+JSON.stringify(e)+".");},p.prototype.serializeProperty=function(e,t,n){var o,s,u=this,c=e[t],p=i.getType(e,t),f=null===(o=null==p?void 0:p.name)||void 0===o?void 0:o.toLowerCase(),d="array"===f,y="set"===f,v="map"===f,h=n.predicate,g=n.type||p,b=l(g);if(c&&(b||h)){if(d||y){var m=y?Array.from(c):c;return this.serializeObjectArray(m)}if(n.isDictionary||v){if(!v)return this.serializeDictionary(c);var O={};return c.forEach((function(e,t){r(t)?O[t]=e:u.error("Fail to serialize: type of '"+typeof t+"' is not assignable to type 'string'.\nReceived: "+JSON.stringify(t)+".");})),console.log(O),this.serializeDictionary(O)}return this.serializeObject(c)}return "date"===(null===(s=null==g?void 0:g.name)||void 0===s?void 0:s.toLocaleLowerCase())&&a(c)?c.toISOString():c},p}(),y=function(t){var r=i.getBaseClass(t);return r&&r.name?__spreadArray(__spreadArray([],y(r)),[r.name]):[]},v=function(){return function(e){var t=y(e);i.setJsonObject({baseClassNames:t},e);}},h=function(e){return function(t,r,n){var o;if(void 0===r&&t.prototype){var a=i.getParamTypes(t)[n];r=g(t.prototype.constructor).get(n),t=t.prototype,i.setType(a,t,r);}var s=null!==(o=i.getJsonPropertiesMetadata(t))&&void 0!==o?o:{};s[r]=b(r,e),i.setJsonPropertiesMetadata(s,t);}},g=function(e){var t,i=e.toString().split("}")[0].replace(/(\/\*[\s\S]*?\*\/|\/\/.*$)/gm,"").replace(/[\r\t\n\v\f ]/g,""),r=i.length;","===i[r-2]&&(t=i[r-1]);var n=t?new RegExp("(?:(this|"+t+"|\\("+t+"=t.call\\(this(,.)*\\)\\))\\.)([^,;\n}]+)","gm"):new RegExp("(?:(this)\\.)([^,;\n}]+)","gm"),o=new Map,a=/(?:.*(?:constructor|function).*?(?=\())(?:\()(.+?(?=\)))/m.exec(i);if(!a||!a.length)return o;for(var s,l=a[1].split(","),u=function(){var e=s.length-1,t=s[e].split("="),i=l.findIndex((function(e){return e===t[1]}));i>-1&&o.set(i,t[0]);};s=n.exec(i);)u();return o},b=function(e,o){var a={name:e.toString()};return o?r(o)?(a.name=o,a.isNameOverridden=!0,a):(n(o)&&(a=__assign(__assign({},a),o),o.name&&(a.name=o.name,a.isNameOverridden=!0),function(e){if(!e)return !1;var t=i.getParamTypes(e),r=e.length;return (1===r||2===r)&&!t}(o.type)&&(delete a.type,a.predicate=o.type)),a):a};

    var Setting_1;
    const SETTINGS_KEY = "AyaLed";
    const serializer = new d();
    let Setting = Setting_1 = 
    // @ts-ignore
    class Setting {
        constructor() {
            this.ledOn = true;
            this.red = 255;
            this.green = 255;
            this.blue = 255;
        }
        static getLedOn() {
            return this._instance.ledOn;
        }
        static setLedOn(red, green, blue) {
            if (this._instance.ledOn != true) {
                this._instance.ledOn = true;
                this._instance.red = red;
                this._instance.blue = blue;
                this._instance.green = green;
                Setting_1.saveSettingsToLocalStorage();
                Backend.applySettings();
            }
        }
        static setOff() {
            if (this._instance.ledOn != false) {
                this._instance.ledOn = false;
                Setting_1.saveSettingsToLocalStorage();
                Backend.applySettings();
            }
        }
        static setRed(red) {
            if (this._instance.red != red) {
                this._instance.red = red;
                Setting_1.saveSettingsToLocalStorage();
                Backend.applySettings();
            }
        }
        static setGreen(green) {
            if (this._instance.green != green) {
                this._instance.green = green;
                Setting_1.saveSettingsToLocalStorage();
                Backend.applySettings();
            }
        }
        static setBlue(blue) {
            if (this._instance.blue != blue) {
                this._instance.blue = blue;
                Setting_1.saveSettingsToLocalStorage();
                Backend.applySettings();
            }
        }
        static getRed() {
            return this._instance.red;
        }
        static getGreen() {
            return this._instance.green;
        }
        static getBlue() {
            return this._instance.blue;
        }
        static loadSettingsFromLocalStorage() {
            const settingsString = localStorage.getItem(SETTINGS_KEY) || "{}";
            const settingsJson = JSON.parse(settingsString);
            const loadSetting = serializer.deserializeObject(settingsJson, Setting_1);
            this._instance = loadSetting ? loadSetting : new Setting_1();
        }
        static saveSettingsToLocalStorage() {
            const settingsJson = serializer.serializeObject(this._instance);
            const settingsString = JSON.stringify(settingsJson);
            localStorage.setItem(SETTINGS_KEY, settingsString);
        }
    };
    Setting._instance = new Setting_1();
    __decorate([
        h(),
        __metadata("design:type", Boolean)
    ], Setting.prototype, "ledOn", void 0);
    __decorate([
        h(),
        __metadata("design:type", Number)
    ], Setting.prototype, "red", void 0);
    __decorate([
        h(),
        __metadata("design:type", Number)
    ], Setting.prototype, "green", void 0);
    __decorate([
        h(),
        __metadata("design:type", Number)
    ], Setting.prototype, "blue", void 0);
    Setting = Setting_1 = __decorate([
        v()
        // @ts-ignore
        ,
        __metadata("design:paramtypes", [])
    ], Setting);

    class Backend {
        static async init(serverAPI) {
            this.serverAPI = serverAPI;
        }
        static applyLedOn(red, blue, green) {
            console.log(`Applying ledOn ${red} ${green} ${blue}`);
            Backend.serverAPI.callPluginMethod("set_ledOn", { "r": red, "g": green, "b": blue });
        }
        static applyLedOff() {
            console.log("Applying ledOff ");
            Backend.serverAPI.callPluginMethod("set_ledOff", {});
        }
        static throwSuspendEvt() {
            console.log("throwSuspendEvt");
            this.serverAPI.callPluginMethod("receive_suspendEvent", {});
        }
    }
    Backend.applySettings = () => {
        if (Setting.getLedOn()) {
            Backend.applyLedOn(Setting.getRed(), Setting.getGreen(), Setting.getBlue());
        }
        else {
            Backend.applyLedOff();
        }
    };

    const SlowSliderField = (slider) => {
        const [changeValue, SetChangeValue] = React.useState(slider.value);
        const isChanging = React.useRef(false);
        React.useEffect(() => {
            setTimeout(() => {
                //console.debug("changeValue=",changeValue,"slider=",slider.value)
                if (changeValue == slider.value) {
                    slider.onChangeEnd?.call(slider, slider.value);
                    isChanging.current = false;
                }
            }, 500);
        }, [changeValue]);
        return (window.SP_REACT.createElement(SliderField, { value: slider.value, label: slider.label, description: slider.description, min: slider.min, max: slider.max, step: slider.step, notchCount: slider.notchCount, notchLabels: slider.notchLabels, notchTicksVisible: slider.notchTicksVisible, showValue: slider.showValue, resetValue: slider.resetValue, disabled: slider.disabled, editableValue: slider.editableValue, validValues: slider.validValues, valueSuffix: slider.valueSuffix, minimumDpadGranularity: slider.minimumDpadGranularity, onChange: (value) => {
                var tpvalue = value;
                if (slider.changeMax != undefined)
                    tpvalue = slider.changeMax <= value ? slider.changeMax : value;
                if (slider.changeMin != undefined)
                    tpvalue = slider.changeMin >= value ? slider.changeMin : value;
                isChanging.current = true;
                slider.onChange?.call(slider, tpvalue);
                slider.value = tpvalue;
                SetChangeValue(tpvalue);
            } }));
    };

    // from https://medium.com/@pdx.lucasm/canvas-with-react-js-32e133c05258
    const Canvas = (props) => {
        const { draw, options, ...rest } = props;
        //const { context, ...moreConfig } = options;
        const canvasRef = useCanvas(draw);
        return window.SP_REACT.createElement("canvas", { ref: canvasRef, ...rest });
    };
    const useCanvas = (draw) => {
        const canvasRef = React.useRef(null);
        React.useEffect(() => {
            const canvas = canvasRef.current;
            const context = canvas.getContext('2d');
            let frameCount = 0;
            let animationFrameId;
            const render = () => {
                frameCount++;
                draw(context, frameCount);
                animationFrameId = window.requestAnimationFrame(render);
            };
            render();
            return () => {
                window.cancelAnimationFrame(animationFrameId);
            };
        }, [draw]);
        return canvasRef;
    };

    const Content = () => {
        const [ledOn, setledOn] = React.useState(Setting.getLedOn());
        const [currentTargetRed, setCurrentTargetRed] = React.useState(Setting.getRed());
        const [currentTargetGreen, setCurrentTargetGreen] = React.useState(Setting.getGreen());
        const [currentTargetBlue, setCurrentTargetBlue] = React.useState(Setting.getBlue());
        const [currentMark, setCurrentMark] = React.useState(0);
        function onClickCanvas(e) {
            //console.log("canvas click", e);
            const realEvent = e.nativeEvent;
            //console.log("Canvas click @ (" + realEvent.layerX.toString() + ", " + realEvent.layerY.toString() + ")");
            const target = e.currentTarget;
            //console.log("Target dimensions " + target.width.toString() + "x" + target.height.toString());
            const clickX = realEvent.layerX;
            setCurrentMark(clickX);
            const cellwidth = target.width / 150;
            var j = clickX / cellwidth;
            //console.log("j " + j.toString());
            var r = 255, g = 0, b = 0;
            for (var i = 0; i < 150; i++) {
                if (i < 25) {
                    g += 10;
                }
                else if (i > 25 && i < 50) {
                    r -= 10;
                }
                else if (i > 50 && i < 75) {
                    g -= 10;
                    b += 10;
                }
                else if (i > 75 && i < 100) {
                    r += 10;
                }
                else {
                    b -= 10;
                    if (b < 0)
                        b = 0;
                }
                if (i >= j) {
                    setCurrentTargetRed(r);
                    setCurrentTargetGreen(g);
                    setCurrentTargetBlue(b);
                    break;
                }
            }
        }
        function drawCanvas(ctx, frameCount) {
            if (frameCount % 100 > 1) {
                return;
            }
            const width = ctx.canvas.width;
            const height = ctx.canvas.height;
            const cellwidth = width / 150;
            var r = 255, g = 0, b = 0;
            for (var i = 0; i < 150; i++) {
                if (i < 25) {
                    g += 10;
                }
                else if (i > 25 && i < 50) {
                    r -= 10;
                }
                else if (i > 50 && i < 75) {
                    g -= 10;
                    b += 10;
                }
                else if (i > 75 && i < 100) {
                    r += 10;
                }
                else {
                    b -= 10;
                }
                ctx.fillStyle = "rgb(" + r + "," + g + "," + b + ")";
                ctx.fillRect(cellwidth * i, 0, cellwidth, height);
            }
            if (currentMark > 0) {
                ctx.beginPath();
                ctx.fillStyle = "#000000";
                ctx.moveTo(currentMark, 0);
                ctx.lineTo(currentMark + 4, 0);
                ctx.lineTo(currentMark + 2, 4);
                ctx.fill();
                console.log("fill Mark " + currentMark.toString());
            }
        }
        React.useEffect(() => {
            if (ledOn) {
                Setting.setLedOn(currentTargetRed, currentTargetGreen, currentTargetBlue);
            }
            else {
                Setting.setOff();
            }
        }, [ledOn]);
        React.useEffect(() => {
            Setting.setRed(currentTargetRed);
            Setting.setGreen(currentTargetGreen);
            Setting.setBlue(currentTargetBlue);
        }, [currentTargetRed, currentTargetGreen, currentTargetBlue]);
        return (window.SP_REACT.createElement(PanelSection, { title: "\u8BBE\u7F6E" },
            window.SP_REACT.createElement(PanelSectionRow, null,
                window.SP_REACT.createElement(ToggleField, { label: "开启灯效", checked: ledOn, onChange: (value) => {
                        setledOn(value);
                    } })),
            ledOn && window.SP_REACT.createElement(PanelSectionRow, null,
                window.SP_REACT.createElement(Canvas, { draw: drawCanvas, width: 268, height: 50, style: {
                        "width": "268px",
                        "height": "50px",
                        "padding": "0px",
                        "border": "1px solid #1a9fff",
                        //"position":"relative",
                        "background-color": "#1a1f2c",
                        "border-radius": "4px",
                        //"margin":"auto",
                    }, onClick: (e) => onClickCanvas(e) })),
            ledOn && window.SP_REACT.createElement(PanelSectionRow, null,
                window.SP_REACT.createElement(SlowSliderField, { label: "\u7EA2", value: currentTargetRed, step: 1, max: 255, min: 0, showValue: true, onChangeEnd: (value) => {
                        setCurrentTargetRed(value);
                    } })),
            ledOn && window.SP_REACT.createElement(PanelSectionRow, null,
                window.SP_REACT.createElement(SlowSliderField, { label: "\u7EFF", value: currentTargetGreen, step: 1, max: 255, min: 0, showValue: true, onChangeEnd: (value) => {
                        setCurrentTargetGreen(value);
                    } })),
            ledOn && window.SP_REACT.createElement(PanelSectionRow, null,
                window.SP_REACT.createElement(SlowSliderField, { label: "\u84DD", value: currentTargetBlue, step: 1, max: 255, min: 0, showValue: true, onChangeEnd: (value) => {
                        setCurrentTargetBlue(value);
                    } }))));
    };
    var index = definePlugin((serverApi) => {
        Setting.loadSettingsFromLocalStorage();
        Backend.init(serverApi);
        Backend.applySettings();
        SteamClient.System.RegisterForOnResumeFromSuspend(async () => {
            Backend.applySettings();
            console.log("结束休眠");
        });
        return {
            title: window.SP_REACT.createElement("div", { className: staticClasses.Title }, "ayaled"),
            content: window.SP_REACT.createElement(Content, null),
            icon: window.SP_REACT.createElement(FaLightbulb, null),
            onDismount() {
            },
        };
    });

    return index;

})(SP_REACT);
