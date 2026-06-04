/** @jsxImportSource @emotion/react */


import { ErrorBoundary } from "react-error-boundary"
import { Fragment, useCallback, useContext, useEffect, useState } from "react"
import { ColorModeContext, EventLoopContext } from "$/utils/context"
import { Event, getBackendURL, isTrue, refs } from "$/utils/state"
import { jsx, keyframes } from "@emotion/react"
import { WifiOffIcon as LucideWifiOffIcon } from "lucide-react"
import { toast, Toaster } from "sonner"
import env from "$/env.json"
import { Box as RadixThemesBox, Flex as RadixThemesFlex, Link as RadixThemesLink, Table as RadixThemesTable, Text as RadixThemesText } from "@radix-ui/themes"
import NextLink from "next/link"
import NextHead from "next/head"



export function Div_602c14884fa2de27f522fe8f94374b02 () {
  
  const [addEvents, connectErrors] = useContext(EventLoopContext);





  
  return (
    <div css={({ ["position"] : "fixed", ["width"] : "100vw", ["height"] : "0" })} title={("Connection Error: "+((connectErrors.length > 0) ? connectErrors[connectErrors.length - 1].message : ''))}>

<Fragment_f2f0916d2fcc08b7cdf76cec697f0750/>
</div>
  )
}

const pulse = keyframes`
    0% {
        opacity: 0;
    }
    100% {
        opacity: 1;
    }
`


export function Toaster_6e6ebf8d7ce589d59b7d382fb7576edf () {
  
  const { resolvedColorMode } = useContext(ColorModeContext)

  refs['__toast'] = toast
  const [addEvents, connectErrors] = useContext(EventLoopContext);
  const toast_props = ({ ["description"] : ("Check if server is reachable at "+getBackendURL(env.EVENT).href), ["closeButton"] : true, ["duration"] : 120000, ["id"] : "websocket-error" });
  const [userDismissed, setUserDismissed] = useState(false);
  (useEffect(
() => {
    if ((connectErrors.length >= 2)) {
        if (!userDismissed) {
            toast.error(
                `Cannot connect to server: ${((connectErrors.length > 0) ? connectErrors[connectErrors.length - 1].message : '')}.`,
                {...toast_props, onDismiss: () => setUserDismissed(true)},
            )
        }
    } else {
        toast.dismiss("websocket-error");
        setUserDismissed(false);  // after reconnection reset dismissed state
    }
}
, [connectErrors]))




  
  return (
    <Toaster closeButton={false} expand={true} position={"bottom-right"} richColors={true} theme={resolvedColorMode}/>
  )
}

export function Fragment_f2f0916d2fcc08b7cdf76cec697f0750 () {
  
  const [addEvents, connectErrors] = useContext(EventLoopContext);





  
  return (
    <Fragment>

{isTrue((connectErrors.length > 0)) ? (
  <Fragment>

<LucideWifiOffIcon css={({ ["color"] : "crimson", ["zIndex"] : 9999, ["position"] : "fixed", ["bottom"] : "33px", ["right"] : "33px", ["animation"] : (pulse+" 1s infinite") })} size={32}/>
</Fragment>
) : (
  <Fragment/>
)}
</Fragment>
  )
}

export function Errorboundary_574175c0f0aa7439d9cce4a927ec74c2 () {
  
  const [addEvents, connectErrors] = useContext(EventLoopContext);


  const on_error_0f5dbf674521530422d73a7946faf6d4 = useCallback(((_error, _info) => (addEvents([(Event("reflex___state____state.reflex___state____frontend_event_exception_state.handle_frontend_exception", ({ ["stack"] : _error["stack"], ["component_stack"] : _info["componentStack"] }), ({  })))], [_error, _info], ({  })))), [addEvents, Event])



  
  return (
    <ErrorBoundary fallbackRender={((event_args) => (jsx("div", ({ ["css"] : ({ ["height"] : "100%", ["width"] : "100%", ["position"] : "absolute", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" }) }), (jsx("div", ({ ["css"] : ({ ["display"] : "flex", ["flexDirection"] : "column", ["gap"] : "1rem" }) }), (jsx("div", ({ ["css"] : ({ ["display"] : "flex", ["flexDirection"] : "column", ["gap"] : "1rem", ["maxWidth"] : "50ch", ["border"] : "1px solid #888888", ["borderRadius"] : "0.25rem", ["padding"] : "1rem" }) }), (jsx("h2", ({ ["css"] : ({ ["fontSize"] : "1.25rem", ["fontWeight"] : "bold" }) }), (jsx(Fragment, ({  }), "An error occurred while rendering this page.")))), (jsx("p", ({ ["css"] : ({ ["opacity"] : "0.75" }) }), (jsx(Fragment, ({  }), "This is an error with the application itself.")))), (jsx("details", ({  }), (jsx("summary", ({ ["css"] : ({ ["padding"] : "0.5rem" }) }), (jsx(Fragment, ({  }), "Error message")))), (jsx("div", ({ ["css"] : ({ ["width"] : "100%", ["maxHeight"] : "50vh", ["overflow"] : "auto", ["background"] : "#000", ["color"] : "#fff", ["borderRadius"] : "0.25rem" }) }), (jsx("div", ({ ["css"] : ({ ["padding"] : "0.5rem", ["width"] : "fit-content" }) }), (jsx("pre", ({  }), (jsx(Fragment, ({  }), event_args.error.stack)))))))), (jsx("button", ({ ["css"] : ({ ["padding"] : "0.35rem 0.75rem", ["margin"] : "0.5rem", ["background"] : "#fff", ["color"] : "#000", ["border"] : "1px solid #000", ["borderRadius"] : "0.25rem", ["fontWeight"] : "bold" }), ["onClick"] : ((...args) => (addEvents([(Event("_call_function", ({ ["function"] : (() => (navigator["clipboard"]["writeText"](event_args.error.stack))), ["callback"] : null }), ({  })))], args, ({  })))) }), (jsx(Fragment, ({  }), "Copy")))))))), (jsx("hr", ({ ["css"] : ({ ["borderColor"] : "currentColor", ["opacity"] : "0.25" }) }))), (jsx("a", ({ ["href"] : "https://reflex.dev" }), (jsx("div", ({ ["css"] : ({ ["display"] : "flex", ["alignItems"] : "baseline", ["justifyContent"] : "center", ["fontFamily"] : "monospace", ["--default-font-family"] : "monospace", ["gap"] : "0.5rem" }) }), (jsx(Fragment, ({  }), "Built with ")), (jsx("svg", ({ ["css"] : ({ ["viewBox"] : "0 0 56 12", ["fill"] : "currentColor" }), ["height"] : "12", ["width"] : "56", ["xmlns"] : "http://www.w3.org/2000/svg" }), (jsx("path", ({ ["d"] : "M0 11.5999V0.399902H8.96V4.8799H6.72V2.6399H2.24V4.8799H6.72V7.1199H2.24V11.5999H0ZM6.72 11.5999V7.1199H8.96V11.5999H6.72Z" }))), (jsx("path", ({ ["d"] : "M11.2 11.5999V0.399902H17.92V2.6399H13.44V4.8799H17.92V7.1199H13.44V9.3599H17.92V11.5999H11.2Z" }))), (jsx("path", ({ ["d"] : "M20.16 11.5999V0.399902H26.88V2.6399H22.4V4.8799H26.88V7.1199H22.4V11.5999H20.16Z" }))), (jsx("path", ({ ["d"] : "M29.12 11.5999V0.399902H31.36V9.3599H35.84V11.5999H29.12Z" }))), (jsx("path", ({ ["d"] : "M38.08 11.5999V0.399902H44.8V2.6399H40.32V4.8799H44.8V7.1199H40.32V9.3599H44.8V11.5999H38.08Z" }))), (jsx("path", ({ ["d"] : "M47.04 4.8799V0.399902H49.28V4.8799H47.04ZM53.76 4.8799V0.399902H56V4.8799H53.76ZM49.28 7.1199V4.8799H53.76V7.1199H49.28ZM47.04 11.5999V7.1199H49.28V11.5999H47.04ZM53.76 11.5999V7.1199H56V11.5999H53.76Z" }))))))))))))))} onError={on_error_0f5dbf674521530422d73a7946faf6d4}>

<Fragment>

<Div_602c14884fa2de27f522fe8f94374b02/>
<Toaster_6e6ebf8d7ce589d59b7d382fb7576edf/>
</Fragment>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["width"] : "100%", ["minHeight"] : "100vh" })} direction={"row"} gap={"0"}>

<RadixThemesBox css={({ ["width"] : "14rem", ["background"] : "white", ["borderRight"] : "1px solid #e5e7eb", ["display"] : "flex", ["flexDirection"] : "column", ["height"] : "100vh", ["position"] : "fixed", ["left"] : "0", ["top"] : "0" })}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["gap"] : "0.625rem", ["paddingInlineStart"] : "1.25rem", ["paddingInlineEnd"] : "1.25rem", ["paddingTop"] : "1.25rem", ["paddingBottom"] : "1.25rem", ["borderBottom"] : "1px solid #f3f4f6" })} direction={"row"} gap={"3"}>

<RadixThemesBox css={({ ["width"] : "2rem", ["height"] : "2rem", ["background"] : "#2563eb", ["borderRadius"] : "0.5rem", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-5 h-5 text-white\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z\"/></svg>" })}/>
</RadixThemesBox>
<RadixThemesText as={"p"} css={({ ["fontWeight"] : "bold", ["color"] : "#1f2937", ["fontSize"] : "0.875rem" })}>

{"OA-EPP"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "1", ["paddingInlineStart"] : "0.75rem", ["paddingInlineEnd"] : "0.75rem", ["paddingTop"] : "1rem", ["paddingBottom"] : "1rem", ["flex"] : "1" })} direction={"column"} gap={"3"}>

<RadixThemesLink asChild={true} css={({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/"} passHref={true}>

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u4eea\u8868\u76d8"}
</RadixThemesText>
</RadixThemesFlex>
</NextLink>
</RadixThemesLink>
<RadixThemesLink asChild={true} css={({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/courses"} passHref={true}>

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u8bfe\u7a0b\u5217\u8868"}
</RadixThemesText>
</RadixThemesFlex>
</NextLink>
</RadixThemesLink>
<RadixThemesLink asChild={true} css={({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/assignments"} passHref={true}>

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u4f5c\u4e1a\u63d0\u4ea4"}
</RadixThemesText>
</RadixThemesFlex>
</NextLink>
</RadixThemesLink>
<RadixThemesLink asChild={true} css={({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/grades"} passHref={true}>

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u6210\u7ee9\u4e0e\u53cd\u9988"}
</RadixThemesText>
</RadixThemesFlex>
</NextLink>
</RadixThemesLink>
<RadixThemesLink asChild={true} css={({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/attendance"} passHref={true}>

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u8bfe\u5802\u7b7e\u5230"}
</RadixThemesText>
</RadixThemesFlex>
</NextLink>
</RadixThemesLink>
<RadixThemesLink asChild={true} css={({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/exam"} passHref={true}>

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm bg-blue-50 text-blue-700 font-medium"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u5728\u7ebf\u8003\u8bd5"}
</RadixThemesText>
</RadixThemesFlex>
</NextLink>
</RadixThemesLink>
<RadixThemesLink asChild={true} css={({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/profile"} passHref={true}>

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u4e2a\u4eba\u8d44\u6599"}
</RadixThemesText>
</RadixThemesFlex>
</NextLink>
</RadixThemesLink>
</RadixThemesFlex>
<RadixThemesBox css={({ ["paddingInlineStart"] : "1rem", ["paddingInlineEnd"] : "1rem", ["paddingTop"] : "1rem", ["paddingBottom"] : "1rem", ["borderTop"] : "1px solid #f3f4f6" })}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<RadixThemesBox css={({ ["width"] : "2rem", ["height"] : "2rem", ["borderRadius"] : "9999px", ["background"] : "#dbeafe", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<RadixThemesText as={"p"} css={({ ["fontWeight"] : "bold", ["fontSize"] : "0.875rem", ["color"] : "#1d4ed8" })}>

{"\u5f20"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0" })} direction={"column"} gap={"0"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#1f2937", ["truncate"] : true })}>

{"\u5f20\u4e09"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["truncate"] : true })}>

{"2021001001"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesFlex>
<RadixThemesLink asChild={true} css={({ ["marginTop"] : "0.75rem", ["display"] : "block", ["textAlign"] : "center", ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/login"} passHref={true}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["&:hover"] : ({ ["color"] : "#ef4444" }) })}>

{"\u9000\u51fa\u767b\u5f55"}
</RadixThemesText>
</NextLink>
</RadixThemesLink>
</RadixThemesBox>
</RadixThemesBox>
<RadixThemesBox css={({ ["marginLeft"] : "14rem", ["flex"] : "1", ["padding"] : "2rem", ["background"] : "#f9fafb", ["minHeight"] : "100vh" })}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["width"] : "100%" })} direction={"column"} gap={"0"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.25rem", ["fontWeight"] : "bold", ["color"] : "#1f2937", ["marginBottom"] : "1.5rem" })}>

{"\u5728\u7ebf\u8003\u8bd5"}
</RadixThemesText>
<RadixThemesBox className={"bg-orange-50 border-2 border-orange-400 rounded-xl p-6 mb-6"} css={({ ["width"] : "100%" })}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["width"] : "100%" })} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} direction={"column"} gap={"3"}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["gap"] : "0.5rem", ["marginBottom"] : "0.25rem" })} direction={"row"} gap={"3"}>

<RadixThemesBox className={"animate-pulse"} css={({ ["width"] : "0.625rem", ["height"] : "0.625rem", ["borderRadius"] : "9999px", ["background"] : "#f97316" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "600", ["color"] : "#c2410c" })}>

{"\u8003\u8bd5\u8fdb\u884c\u4e2d"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.125rem", ["fontWeight"] : "bold", ["color"] : "#1f2937" })}>

{"\u5de5\u7a0b\u5b9e\u8df54 \u00b7 \u7b2c11\u5468\u968f\u5802\u6d4b\u9a8c"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280", ["marginTop"] : "0.25rem" })}>

{"\u5171 10 \u9898 | \u603b\u5206 20 \u5206 | \u9650\u65f6 20 \u5206\u949f"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesFlex align={"end"} className={"rx-Stack"} direction={"column"} gap={"3"}>

<RadixThemesText as={"p"} className={"tabular-nums"} css={({ ["fontSize"] : "1.875rem", ["fontWeight"] : "bold", ["color"] : "#f97316", ["fontFamily"] : "'Courier New', monospace", ["--default-font-family"] : "'Courier New', monospace" })}>

{"14:23"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280", ["marginTop"] : "0.25rem" })}>

{"\u5269\u4f59\u65f6\u95f4"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesFlex>
<RadixThemesBox css={({ ["marginBottom"] : "1rem" })}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["width"] : "100%", ["marginBottom"] : "0.25rem" })} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280" })}>

{"\u7b54\u9898\u8fdb\u5ea6"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280" })}>

{"7 / 10 \u9898\u5df2\u4f5c\u7b54"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesBox css={({ ["width"] : "100%", ["background"] : "#e5e7eb", ["height"] : "0.5rem", ["borderRadius"] : "9999px" })}>

<RadixThemesBox css={({ ["width"] : "70.0%", ["height"] : "100%", ["background"] : "#f97316", ["borderRadius"] : "9999px" })}/>
</RadixThemesBox>
</RadixThemesBox>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0.5rem", ["flexWrap"] : "wrap", ["marginBottom"] : "1rem" })} direction={"row"} gap={"3"}>

<RadixThemesBox className={""} css={({ ["width"] : "2rem", ["height"] : "2rem", ["background"] : "#22c55e", ["borderRadius"] : "0.25rem", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "bold", ["color"] : "white" })}>

{"1"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesBox className={""} css={({ ["width"] : "2rem", ["height"] : "2rem", ["background"] : "#22c55e", ["borderRadius"] : "0.25rem", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "bold", ["color"] : "white" })}>

{"2"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesBox className={""} css={({ ["width"] : "2rem", ["height"] : "2rem", ["background"] : "#22c55e", ["borderRadius"] : "0.25rem", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "bold", ["color"] : "white" })}>

{"3"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesBox className={""} css={({ ["width"] : "2rem", ["height"] : "2rem", ["background"] : "#22c55e", ["borderRadius"] : "0.25rem", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "bold", ["color"] : "white" })}>

{"4"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesBox className={""} css={({ ["width"] : "2rem", ["height"] : "2rem", ["background"] : "#22c55e", ["borderRadius"] : "0.25rem", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "bold", ["color"] : "white" })}>

{"5"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesBox className={""} css={({ ["width"] : "2rem", ["height"] : "2rem", ["background"] : "#22c55e", ["borderRadius"] : "0.25rem", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "bold", ["color"] : "white" })}>

{"6"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesBox className={""} css={({ ["width"] : "2rem", ["height"] : "2rem", ["background"] : "#22c55e", ["borderRadius"] : "0.25rem", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "bold", ["color"] : "white" })}>

{"7"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesBox className={"ring-2 ring-orange-300"} css={({ ["width"] : "2rem", ["height"] : "2rem", ["background"] : "#f97316", ["borderRadius"] : "0.25rem", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "bold", ["color"] : "white" })}>

{"8"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesBox className={""} css={({ ["width"] : "2rem", ["height"] : "2rem", ["background"] : "#e5e7eb", ["borderRadius"] : "0.25rem", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "bold", ["color"] : "#6b7280" })}>

{"9"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesBox className={""} css={({ ["width"] : "2rem", ["height"] : "2rem", ["background"] : "#e5e7eb", ["borderRadius"] : "0.25rem", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "bold", ["color"] : "#6b7280" })}>

{"10"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["marginLeft"] : "0.75rem", ["alignSelf"] : "center" })}>

{"\u7eff=\u5df2\u7b54 \u00b7 \u6a59=\u5f53\u524d \u00b7 \u7070=\u672a\u7b54"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesBox>
<RadixThemesBox className={"bg-white rounded-xl border border-gray-200 shadow-sm mb-4"} css={({ ["width"] : "100%" })}>

<RadixThemesFlex align={"center"} className={"rx-Stack px-6 py-4 border-b border-gray-100"} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#4b5563" })}>

{"\u7b2c 8 \u9898 \u00b7 \u5355\u9009\u9898 \u00b7 2 \u5206"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u8349\u7a3f\u5df2\u81ea\u52a8\u4fdd\u5b58 08:14:22"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesBox className={"px-6 py-5"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#1f2937", ["marginBottom"] : "1.25rem" })}>

{"\u5728 Reflex \u6846\u67b6\u4e2d\uff0c\u4e0b\u5217\u54ea\u79cd\u65b9\u5f0f\u662f\u89e6\u53d1 State \u66f4\u65b0\u7684\u6b63\u786e\u65b9\u6cd5\uff1f"}
</RadixThemesText>
<RadixThemesFlex align={"stretch"} className={"rx-Stack"} css={({ ["gap"] : "0.75rem" })} direction={"column"} gap={"3"}>

<RadixThemesBox className={"flex items-start gap-3 p-3 border rounded-lg cursor-pointer border-gray-200 hover:bg-blue-50 hover:border-blue-300"}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<input className={"mt-0.5 text-blue-600"} css={({ ["type"] : "radio" })} defaultChecked={false} name={"q8"}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#374151" })}>

{"A. \u76f4\u63a5\u4fee\u6539 State \u7c7b\u7684\u5b9e\u4f8b\u53d8\u91cf"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesBox>
<RadixThemesBox className={"flex items-start gap-3 p-3 border rounded-lg cursor-pointer border-gray-200 hover:bg-blue-50 hover:border-blue-300"}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<input className={"mt-0.5 text-blue-600"} css={({ ["type"] : "radio" })} defaultChecked={false} name={"q8"}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#374151" })}>

{"B. \u5728\u4e8b\u4ef6\u5904\u7406\u51fd\u6570\u4e2d\u901a\u8fc7 yield \u8fd4\u56de\u72b6\u6001\u66f4\u65b0"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesBox>
<RadixThemesBox className={"flex items-start gap-3 p-3 border rounded-lg cursor-pointer border-blue-400 bg-blue-50"}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<input className={"mt-0.5 text-blue-600"} css={({ ["type"] : "radio" })} defaultChecked={true} name={"q8"}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#374151" })}>

{"C. \u5b9a\u4e49\u4e8b\u4ef6\u5904\u7406\u51fd\u6570\uff08EventHandler\uff09\uff0c\u5728\u5176\u4e2d self.var = value \u8d4b\u503c"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesBox>
<RadixThemesBox className={"flex items-start gap-3 p-3 border rounded-lg cursor-pointer border-gray-200 hover:bg-blue-50 hover:border-blue-300"}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<input className={"mt-0.5 text-blue-600"} css={({ ["type"] : "radio" })} defaultChecked={false} name={"q8"}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#374151" })}>

{"D. \u901a\u8fc7 JavaScript \u8c03\u7528 Reflex \u5185\u7f6e\u5168\u5c40\u51fd\u6570 setState()"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesBox>
</RadixThemesFlex>
</RadixThemesBox>
<RadixThemesFlex align={"center"} className={"rx-Stack px-6 py-4 border-t border-gray-100"} direction={"row"} justify={"between"} gap={"3"}>

<button className={"px-4 py-2 border border-gray-300 text-gray-600 rounded-lg text-sm hover:bg-gray-50"}>

{"\u2190 \u4e0a\u4e00\u9898"}
</button>
<button className={"px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium"}>

{"\u4e0b\u4e00\u9898 \u2192"}
</button>
</RadixThemesFlex>
</RadixThemesBox>
<RadixThemesBox className={"bg-white rounded-xl border border-gray-200 shadow-sm p-5"} css={({ ["width"] : "100%" })}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280" })}>

<RadixThemesText as={"span"} css={({ ["fontWeight"] : "500", ["color"] : "#ef4444" })}>

{"\u6ce8\u610f\uff1a"}
</RadixThemesText>
{"\u63d0\u4ea4\u540e\u4e0d\u53ef\u4fee\u6539\u3002\u622a\u6b62\u65f6\u95f4\u5230\u5c06\u81ea\u52a8\u63d0\u4ea4\u5f53\u524d\u5df2\u4f5c\u7b54\u5185\u5bb9\u3002"}
</RadixThemesText>
<button className={"px-6 py-2.5 bg-red-500 hover:bg-red-600 text-white font-bold rounded-lg text-sm shadow"}>

{"\u63d0\u4ea4\u8bd5\u5377"}
</button>
</RadixThemesFlex>
</RadixThemesBox>
<RadixThemesBox className={"bg-white rounded-xl border border-gray-200 shadow-sm mt-6"} css={({ ["width"] : "100%" })}>

<RadixThemesText as={"p"} className={"px-5 py-4 border-b border-gray-100"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "600", ["color"] : "#1f2937" })}>

{"\u5386\u53f2\u8003\u8bd5\u6210\u7ee9"}
</RadixThemesText>
<RadixThemesBox className={"px-5 py-4"}>

<RadixThemesTable.Root css={({ ["width"] : "100%" })}>

<RadixThemesTable.Header>

<RadixThemesTable.Row>

<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u8003\u8bd5\u540d\u79f0"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u8003\u8bd5\u65f6\u95f4"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u603b\u5206"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u5f97\u5206"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u72b6\u6001"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u64cd\u4f5c"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
</RadixThemesTable.Row>
</RadixThemesTable.Header>
<RadixThemesTable.Body>

<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#374151" })}>

{"\u7b2c10\u5468\u968f\u5802\u6d4b\u9a8c"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280" })}>

{"2025-05-18"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#4b5563" })}>

{"20"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontWeight"] : "bold", ["color"] : "#16a34a", ["fontSize"] : "0.875rem" })}>

{"18"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} className={"px-2 py-0.5 bg-green-100 text-green-600 rounded text-xs font-medium"}>

{"\u5df2\u6279\u6539"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#3b82f6", ["&:hover"] : ({ ["textDecoration"] : "underline" }) })}>

{"\u67e5\u770b\u8be6\u60c5"}
</RadixThemesText>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#374151" })}>

{"\u7b2c8\u5468\u968f\u5802\u6d4b\u9a8c"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280" })}>

{"2025-05-04"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#4b5563" })}>

{"20"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontWeight"] : "bold", ["color"] : "#16a34a", ["fontSize"] : "0.875rem" })}>

{"16"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} className={"px-2 py-0.5 bg-green-100 text-green-600 rounded text-xs font-medium"}>

{"\u5df2\u6279\u6539"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#3b82f6", ["&:hover"] : ({ ["textDecoration"] : "underline" }) })}>

{"\u67e5\u770b\u8be6\u60c5"}
</RadixThemesText>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#374151" })}>

{"\u671f\u4e2d\u8003\u8bd5"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280" })}>

{"2025-04-20"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#4b5563" })}>

{"50"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontWeight"] : "bold", ["color"] : "#ca8a04", ["fontSize"] : "0.875rem" })}>

{"38"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} className={"px-2 py-0.5 bg-green-100 text-green-600 rounded text-xs font-medium"}>

{"\u5df2\u6279\u6539"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#3b82f6", ["&:hover"] : ({ ["textDecoration"] : "underline" }) })}>

{"\u67e5\u770b\u8be6\u60c5"}
</RadixThemesText>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#374151" })}>

{"\u7b2c5\u5468\u968f\u5802\u6d4b\u9a8c"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280" })}>

{"2025-04-13"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#4b5563" })}>

{"20"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontWeight"] : "bold", ["color"] : "#9ca3af", ["fontSize"] : "0.875rem" })}>

{"\u2014"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} className={"px-2 py-0.5 bg-yellow-100 text-yellow-600 rounded text-xs font-medium"}>

{"\u5f85\u6279\u6539"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#3b82f6", ["&:hover"] : ({ ["textDecoration"] : "underline" }) })}>

{"\u67e5\u770b\u8be6\u60c5"}
</RadixThemesText>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
</RadixThemesTable.Body>
</RadixThemesTable.Root>
</RadixThemesBox>
</RadixThemesBox>
</RadixThemesFlex>
</RadixThemesBox>
</RadixThemesFlex>
<NextHead>

<title>

{"OA-EPP \u00b7 \u5728\u7ebf\u8003\u8bd5"}
</title>
<meta content={"favicon.ico"} property={"og:image"}/>
</NextHead>
</ErrorBoundary>
  )
}

export default function Component() {
    




  return (
    <Errorboundary_574175c0f0aa7439d9cce4a927ec74c2/>
  )
}
