/** @jsxImportSource @emotion/react */


import { ErrorBoundary } from "react-error-boundary"
import { Fragment, useCallback, useContext, useEffect, useState } from "react"
import { ColorModeContext, EventLoopContext } from "$/utils/context"
import { Event, getBackendURL, isTrue, refs } from "$/utils/state"
import { jsx, keyframes } from "@emotion/react"
import { WifiOffIcon as LucideWifiOffIcon } from "lucide-react"
import { toast, Toaster } from "sonner"
import env from "$/env.json"
import { Box as RadixThemesBox, Flex as RadixThemesFlex, Grid as RadixThemesGrid, Link as RadixThemesLink, Table as RadixThemesTable, Text as RadixThemesText } from "@radix-ui/themes"
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


export function Errorboundary_02bdfd636cd310f2083ee3edede3370c () {
  
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

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm bg-blue-50 text-blue-700 font-medium"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u8bfe\u5802\u7b7e\u5230"}
</RadixThemesText>
</RadixThemesFlex>
</NextLink>
</RadixThemesLink>
<RadixThemesLink asChild={true} css={({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/exam"} passHref={true}>

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

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

{"\u8bfe\u5802\u7b7e\u5230"}
</RadixThemesText>
<RadixThemesBox className={"bg-green-50 border-2 border-green-400 rounded-xl p-6 mb-6"} css={({ ["width"] : "100%" })}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["width"] : "100%" })} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} direction={"column"} gap={"3"}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["gap"] : "0.5rem", ["marginBottom"] : "0.25rem" })} direction={"row"} gap={"3"}>

<RadixThemesBox className={"animate-pulse"} css={({ ["width"] : "0.625rem", ["height"] : "0.625rem", ["borderRadius"] : "9999px", ["background"] : "#22c55e" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "600", ["color"] : "#15803d" })}>

{"\u6b63\u5728\u8fdb\u884c\u4e2d"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.125rem", ["fontWeight"] : "bold", ["color"] : "#1f2937", ["marginBottom"] : "0.25rem" })}>

{"\u5de5\u7a0b\u5b9e\u8df54 \u00b7 \u7b2c11\u5468\u8bfe\u5802"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280" })}>

{"\u6559\u5e08\uff1a\u674e\u8001\u5e08 | \u5730\u70b9\uff1a\u6559\u5b66\u697c B306 | \u8bfe\u7a0b\uff1a2025-05-25 08:00"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesFlex align={"end"} className={"rx-Stack"} direction={"column"} gap={"3"}>

<RadixThemesText as={"p"} className={"tabular-nums"} css={({ ["fontSize"] : "1.875rem", ["fontWeight"] : "bold", ["color"] : "#ef4444", ["fontFamily"] : "'Courier New', monospace", ["--default-font-family"] : "'Courier New', monospace" })}>

{"00:42"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280", ["marginTop"] : "0.25rem" })}>

{"\u5269\u4f59\u79d2\u6570"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesFlex>
<RadixThemesBox css={({ ["marginTop"] : "1rem", ["marginBottom"] : "1rem" })}>

<RadixThemesBox css={({ ["width"] : "100%", ["background"] : "#e5e7eb", ["height"] : "0.5rem", ["borderRadius"] : "9999px" })}>

<RadixThemesBox css={({ ["width"] : "70%", ["height"] : "100%", ["background"] : "#22c55e", ["borderRadius"] : "9999px" })}/>
</RadixThemesBox>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["width"] : "100%", ["marginTop"] : "0.25rem" })} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u7b7e\u5230\u5f00\u59cb"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"60 \u79d2\u7a97\u53e3\u671f"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesBox>
<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["gap"] : "0.75rem", ["marginBottom"] : "0.75rem" })} direction={"row"} gap={"3"}>

<button className={"px-8 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg text-base shadow"}>

{"\u786e\u8ba4\u7b7e\u5230"}
</button>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280" })}>

{"\u7b7e\u5230\u524d\u8bf7\u786e\u8ba4\u5df2\u5728\u6559\u5ba4\u5185"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesBox className={"mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg"}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0.5rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z\"/><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M15 11a3 3 0 11-6 0 3 3 0 016 0z\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#a16207" })}>

{"\u5730\u7406\u56f4\u680f\u9a8c\u8bc1\u5df2\u542f\u7528\uff1a\u7cfb\u7edf\u5c06\u6838\u9a8c\u60a8\u5f53\u524d\u4f4d\u7f6e\u662f\u5426\u5728 B306 \u6559\u5ba4\u8303\u56f4\u5185\uff08\u534a\u5f84 50 \u7c73\uff09\u3002\u82e5\u5b9a\u4f4d\u5931\u8d25\uff0c\u8bf7\u5141\u8bb8\u6d4f\u89c8\u5668\u8bbf\u95ee\u4f4d\u7f6e\u6743\u9650\u3002"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesBox>
</RadixThemesBox>
<RadixThemesBox className={"bg-white rounded-xl border border-gray-200 shadow-sm mb-6"} css={({ ["width"] : "100%" })}>

<RadixThemesFlex align={"center"} className={"rx-Stack px-5 py-4 border-b border-gray-100"} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "600", ["color"] : "#1f2937" })}>

{"\u672c\u5b66\u671f\u51fa\u52e4\u8bb0\u5f55"}
</RadixThemesText>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "1rem" })} direction={"row"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280" })}>

{"\u603b\u8ba1 18 \u6b21"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#16a34a" })}>

{"\u51fa\u52e4 15"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#eab308" })}>

{"\u8fdf\u5230 1"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#ef4444" })}>

{"\u7f3a\u52e4 2"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesFlex>
<RadixThemesBox className={"px-5 pt-4 pb-2"}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280", ["width"] : "4rem" })}>

{"\u51fa\u52e4\u7387"}
</RadixThemesText>
<RadixThemesBox css={({ ["flex"] : "1", ["background"] : "#f3f4f6", ["height"] : "0.75rem", ["borderRadius"] : "9999px" })}>

<RadixThemesBox css={({ ["width"] : "83.3%", ["height"] : "100%", ["background"] : "#3b82f6", ["borderRadius"] : "9999px" })}/>
</RadixThemesBox>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "bold", ["color"] : "#2563eb", ["width"] : "3rem", ["textAlign"] : "right" })}>

{"83.3%"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesBox>
<RadixThemesBox className={"px-5 py-4"}>

<RadixThemesTable.Root css={({ ["width"] : "100%" })}>

<RadixThemesTable.Header>

<RadixThemesTable.Row>

<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u5468\u6b21"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u65e5\u671f"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u8bfe\u7a0b"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u7b7e\u5230\u65f6\u95f4"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u72b6\u6001"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
</RadixThemesTable.Row>
</RadixThemesTable.Header>
<RadixThemesTable.Body>

<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280" })}>

{"\u7b2c11\u5468"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"2025-05-25"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#4b5563" })}>

{"\u5de5\u7a0b\u5b9e\u8df54"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280" })}>

{"\u2014"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} className={"px-2 py-0.5 bg-blue-100 text-blue-600 rounded text-xs font-medium"}>

{"\u7b7e\u5230\u4e2d"}
</RadixThemesText>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280" })}>

{"\u7b2c10\u5468"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"2025-05-18"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#4b5563" })}>

{"\u5de5\u7a0b\u5b9e\u8df54"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280" })}>

{"08:02:15"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} className={"px-2 py-0.5 bg-green-100 text-green-600 rounded text-xs font-medium"}>

{"\u51fa\u52e4"}
</RadixThemesText>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280" })}>

{"\u7b2c9\u5468"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"2025-05-11"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#4b5563" })}>

{"\u5de5\u7a0b\u5b9e\u8df54"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280" })}>

{"08:00:48"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} className={"px-2 py-0.5 bg-green-100 text-green-600 rounded text-xs font-medium"}>

{"\u51fa\u52e4"}
</RadixThemesText>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280" })}>

{"\u7b2c8\u5468"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"2025-05-04"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#4b5563" })}>

{"\u5de5\u7a0b\u5b9e\u8df54"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280" })}>

{"08:05:33"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} className={"px-2 py-0.5 bg-yellow-100 text-yellow-600 rounded text-xs font-medium"}>

{"\u8fdf\u5230"}
</RadixThemesText>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280" })}>

{"\u7b2c7\u5468"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"2025-04-27"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#4b5563" })}>

{"\u5de5\u7a0b\u5b9e\u8df54"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280" })}>

{"\u2014"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} className={"px-2 py-0.5 bg-red-100 text-red-600 rounded text-xs font-medium"}>

{"\u7f3a\u52e4"}
</RadixThemesText>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280" })}>

{"\u7b2c6\u5468"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"2025-04-20"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#4b5563" })}>

{"\u5de5\u7a0b\u5b9e\u8df54"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280" })}>

{"08:01:20"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} className={"px-2 py-0.5 bg-green-100 text-green-600 rounded text-xs font-medium"}>

{"\u51fa\u52e4"}
</RadixThemesText>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280" })}>

{"\u7b2c5\u5468"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"2025-04-13"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#4b5563" })}>

{"\u5de5\u7a0b\u5b9e\u8df54"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280" })}>

{"\u2014"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} className={"px-2 py-0.5 bg-red-100 text-red-600 rounded text-xs font-medium"}>

{"\u7f3a\u52e4"}
</RadixThemesText>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
</RadixThemesTable.Body>
</RadixThemesTable.Root>
</RadixThemesBox>
</RadixThemesBox>
<RadixThemesBox className={"bg-white rounded-xl border border-gray-200 shadow-sm"} css={({ ["width"] : "100%" })}>

<RadixThemesText as={"p"} className={"px-5 py-4 border-b border-gray-100"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "600", ["color"] : "#1f2937" })}>

{"\u51fa\u52e4\u5f97\u5206\u8ba1\u7b97\u89c4\u5219"}
</RadixThemesText>
<RadixThemesBox className={"px-5 py-4"}>

<RadixThemesGrid css={({ ["gridTemplateColumns"] : "repeat(3, 1fr)", ["gap"] : "1rem", ["marginBottom"] : "1rem" })}>

<RadixThemesBox className={"bg-blue-50 rounded-lg p-4 text-center"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.5rem", ["fontWeight"] : "bold", ["color"] : "#2563eb" })}>

{"15"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280", ["marginTop"] : "0.25rem" })}>

{"\u603b\u5206"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesBox className={"bg-green-50 rounded-lg p-4 text-center"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.5rem", ["fontWeight"] : "bold", ["color"] : "#16a34a" })}>

{"12.5"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280", ["marginTop"] : "0.25rem" })}>

{"\u5f53\u524d\u5f97\u5206\uff08\u4f30\u7b97\uff09"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesBox className={"bg-yellow-50 rounded-lg p-4 text-center"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.5rem", ["fontWeight"] : "bold", ["color"] : "#ca8a04" })}>

{"83.3%"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280", ["marginTop"] : "0.25rem" })}>

{"\u51fa\u52e4\u7387"}
</RadixThemesText>
</RadixThemesBox>
</RadixThemesGrid>
<RadixThemesFlex align={"stretch"} className={"rx-Stack"} css={({ ["gap"] : "0.25rem" })} direction={"column"} gap={"3"}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0.5rem" })} direction={"row"} gap={"3"}>

<RadixThemesBox className={"bg-green-100 rounded flex-shrink-0 mt-0.5"} css={({ ["width"] : "1rem", ["height"] : "1rem" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#4b5563" })}>

{"\u51fa\u52e4\uff1a\u8ba1\u4e3a 1 \u6b21"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0.5rem" })} direction={"row"} gap={"3"}>

<RadixThemesBox className={"bg-yellow-100 rounded flex-shrink-0 mt-0.5"} css={({ ["width"] : "1rem", ["height"] : "1rem" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#4b5563" })}>

{"\u8fdf\u5230\uff1a\u8ba1\u4e3a 0.5 \u6b21"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0.5rem" })} direction={"row"} gap={"3"}>

<RadixThemesBox className={"bg-red-100 rounded flex-shrink-0 mt-0.5"} css={({ ["width"] : "1rem", ["height"] : "1rem" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#4b5563" })}>

{"\u7f3a\u52e4\uff1a\u8ba1\u4e3a 0 \u6b21\uff0c\u7d2f\u8ba1\u7f3a\u8bfe\u8d85 1/3 \u53d6\u6d88\u8003\u8bd5\u8d44\u683c"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesFlex>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["marginTop"] : "0.5rem" })}>

{"\u51fa\u52e4\u5f97\u5206 = \u51fa\u52e4\u7387 \u00d7 \u672c\u9879\u6ee1\u5206\uff0815 \u5206\uff09\uff0c\u6700\u7ec8\u6210\u7ee9\u53d1\u5e03\u540e\u4ee5\u6559\u5e08\u786e\u8ba4\u4e3a\u51c6\u3002"}
</RadixThemesText>
</RadixThemesBox>
</RadixThemesBox>
</RadixThemesFlex>
</RadixThemesBox>
</RadixThemesFlex>
<NextHead>

<title>

{"OA-EPP \u00b7 \u8bfe\u5802\u7b7e\u5230"}
</title>
<meta content={"favicon.ico"} property={"og:image"}/>
</NextHead>
</ErrorBoundary>
  )
}

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

export default function Component() {
    




  return (
    <Errorboundary_02bdfd636cd310f2083ee3edede3370c/>
  )
}
