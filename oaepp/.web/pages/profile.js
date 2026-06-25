/** @jsxImportSource @emotion/react */


import { ErrorBoundary } from "react-error-boundary"
import { Fragment, useCallback, useContext, useEffect, useState } from "react"
import { ColorModeContext, EventLoopContext } from "$/utils/context"
import { Event, getBackendURL, isTrue, refs } from "$/utils/state"
import { jsx, keyframes } from "@emotion/react"
import { WifiOffIcon as LucideWifiOffIcon } from "lucide-react"
import { toast, Toaster } from "sonner"
import env from "$/env.json"
import { Box as RadixThemesBox, Flex as RadixThemesFlex, Grid as RadixThemesGrid, Link as RadixThemesLink, Text as RadixThemesText } from "@radix-ui/themes"
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

export function Errorboundary_8e6ba4ce89760365b9941668bf3b8921 () {
  
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

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm bg-blue-50 text-blue-700 font-medium"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

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

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["width"] : "100%", ["maxWidth"] : "56rem" })} direction={"column"} gap={"0"}>

<RadixThemesBox css={({ ["marginBottom"] : "1.5rem", ["width"] : "100%" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.25rem", ["fontWeight"] : "bold", ["color"] : "#1f2937" })}>

{"\u4e2a\u4eba\u8d44\u6599"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#9ca3af", ["marginTop"] : "0.125rem" })}>

{"\u7ba1\u7406\u8d26\u53f7\u4fe1\u606f\u4e0e GitHub \u7ed1\u5b9a"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesBox className={"bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-6"} css={({ ["width"] : "100%" })}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["gap"] : "1.25rem", ["marginBottom"] : "1.5rem" })} direction={"row"} gap={"3"}>

<RadixThemesBox css={({ ["width"] : "4rem", ["height"] : "4rem", ["borderRadius"] : "9999px", ["background"] : "#dbeafe", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.5rem", ["fontWeight"] : "bold", ["color"] : "#1d4ed8" })}>

{"\u5f20"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0" })} direction={"column"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.125rem", ["fontWeight"] : "bold", ["color"] : "#1f2937" })}>

{"\u5f20\u4e09"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#9ca3af" })}>

{"\u5b66\u53f7\uff1a2021001001 \u00b7 \u73ed\u7ea7\uff1a\u5de5\u7a0b\u5b9e\u8df5\u73edA"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesFlex>
<RadixThemesGrid css={({ ["gridTemplateColumns"] : "repeat(2, 1fr)", ["gap"] : "1.25rem", ["marginBottom"] : "1.25rem" })}>

<RadixThemesBox>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#6b7280", ["marginBottom"] : "0.25rem" })}>

{"\u59d3\u540d"}
</RadixThemesText>
<input className={"w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none border-gray-200 text-gray-800 focus:ring-2 focus:ring-blue-400"} disabled={false} value={"\u5f20\u4e09"}/>
</RadixThemesBox>
<RadixThemesBox>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#6b7280", ["marginBottom"] : "0.25rem" })}>

{"\u5b66\u53f7\uff08\u53ea\u8bfb\uff09"}
</RadixThemesText>
<input className={"w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none border-gray-100 bg-gray-50 text-gray-500 cursor-not-allowed"} disabled={true} value={"2021001001"}/>
</RadixThemesBox>
<RadixThemesBox>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#6b7280", ["marginBottom"] : "0.25rem" })}>

{"\u90ae\u7bb1"}
</RadixThemesText>
<input className={"w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none border-gray-200 text-gray-800 focus:ring-2 focus:ring-blue-400"} disabled={false} value={"zhangsan@example.edu.cn"}/>
</RadixThemesBox>
<RadixThemesBox>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#6b7280", ["marginBottom"] : "0.25rem" })}>

{"\u73ed\u7ea7"}
</RadixThemesText>
<input className={"w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none border-gray-100 bg-gray-50 text-gray-500 cursor-not-allowed"} disabled={true} value={"\u5de5\u7a0b\u5b9e\u8df5\u73edA"}/>
</RadixThemesBox>
</RadixThemesGrid>
<RadixThemesFlex align={"start"} className={"rx-Stack"} direction={"row"} justify={"end"} gap={"3"}>

<button className={"bg-blue-600 hover:bg-blue-700 text-white text-sm px-5 py-2 rounded-lg transition"}>

{"\u4fdd\u5b58\u4fee\u6539"}
</button>
</RadixThemesFlex>
</RadixThemesBox>
<RadixThemesBox className={"bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-6"} css={({ ["width"] : "100%" })}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["marginBottom"] : "1rem" })} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-6 h-6 text-gray-700\" fill=\"currentColor\" viewBox=\"0 0 24 24\"><path d=\"M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.4041.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "600", ["color"] : "#374151" })}>

{"GitHub \u8d26\u53f7\u7ed1\u5b9a"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesText as={"p"} className={"text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full"}>

{"\u5df2\u7ed1\u5b9a \u00b7 \u5ba1\u6838\u901a\u8fc7"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesFlex align={"stretch"} className={"rx-Stack"} css={({ ["gap"] : "0", ["marginBottom"] : "0.75rem" })} direction={"column"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#6b7280", ["marginBottom"] : "0.25rem" })}>

{"GitHub \u7528\u6237\u540d"}
</RadixThemesText>
<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["gap"] : "0.5rem" })} direction={"row"} gap={"3"}>

<input className={"flex-1 border border-gray-100 bg-gray-50 rounded-lg px-3 py-2.5 text-sm text-gray-600 cursor-not-allowed"} disabled={true} value={"zhangsan-dev"}/>
<RadixThemesLink asChild={true} css={({ ["fontSize"] : "0.75rem", ["color"] : "#3b82f6", ["&:hover"] : ({ ["textDecoration"] : "underline" }), ["whiteSpace"] : "nowrap" })}>

<NextLink href={"https://github.com/zhangsan-dev"} passHref={true}>

{"\u8bbf\u95ee\u4e3b\u9875 \u2192"}
</NextLink>
</RadixThemesLink>
</RadixThemesFlex>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["marginTop"] : "0.25rem" })}>

{"GitHub \u5b9e\u540d\uff1aZhang San \u00b7 \u6838\u67e5\u901a\u8fc7 \u2713"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesBox className={"bg-yellow-50 border border-yellow-100 rounded-lg px-4 py-3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#a16207" })}>

{"\u5982\u9700\u4fee\u6539\u7ed1\u5b9a\u8d26\u53f7\uff0c\u8bf7\u5411\u6559\u5e08\u7533\u8bf7\u89e3\u9664\u5f53\u524d\u7ed1\u5b9a\u540e\u91cd\u65b0\u63d0\u4ea4\u3002"}
</RadixThemesText>
</RadixThemesBox>
</RadixThemesBox>
<RadixThemesBox className={"bg-white rounded-xl border border-gray-100 shadow-sm p-6"} css={({ ["width"] : "100%" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "600", ["color"] : "#374151", ["marginBottom"] : "1rem" })}>

{"\u4fee\u6539\u5bc6\u7801"}
</RadixThemesText>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "1rem", ["maxWidth"] : "24rem" })} direction={"column"} gap={"3"}>

<RadixThemesBox css={({ ["width"] : "100%" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#6b7280", ["marginBottom"] : "0.25rem" })}>

{"\u5f53\u524d\u5bc6\u7801"}
</RadixThemesText>
<input className={"w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"} css={({ ["type"] : "password" })} placeholder={"\u8bf7\u8f93\u5165\u5f53\u524d\u5bc6\u7801"}/>
</RadixThemesBox>
<RadixThemesBox css={({ ["width"] : "100%" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#6b7280", ["marginBottom"] : "0.25rem" })}>

{"\u65b0\u5bc6\u7801"}
</RadixThemesText>
<input className={"w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"} css={({ ["type"] : "password" })} placeholder={"\u81f3\u5c11 8 \u4f4d\uff0c\u5305\u542b\u5b57\u6bcd\u548c\u6570\u5b57"}/>
</RadixThemesBox>
<RadixThemesBox css={({ ["width"] : "100%" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#6b7280", ["marginBottom"] : "0.25rem" })}>

{"\u786e\u8ba4\u65b0\u5bc6\u7801"}
</RadixThemesText>
<input className={"w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"} css={({ ["type"] : "password" })} placeholder={"\u518d\u6b21\u8f93\u5165\u65b0\u5bc6\u7801"}/>
</RadixThemesBox>
<button className={"bg-blue-600 hover:bg-blue-700 text-white text-sm px-5 py-2 rounded-lg transition"}>

{"\u786e\u8ba4\u4fee\u6539\u5bc6\u7801"}
</button>
</RadixThemesFlex>
</RadixThemesBox>
</RadixThemesFlex>
</RadixThemesBox>
</RadixThemesFlex>
<NextHead>

<title>

{"OA-EPP \u00b7 \u4e2a\u4eba\u8d44\u6599"}
</title>
<meta content={"favicon.ico"} property={"og:image"}/>
</NextHead>
</ErrorBoundary>
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

export default function Component() {
    




  return (
    <Errorboundary_8e6ba4ce89760365b9941668bf3b8921/>
  )
}
