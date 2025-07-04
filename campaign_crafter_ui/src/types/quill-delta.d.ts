// Basic type declaration for the 'quill-delta' module
// This helps TypeScript recognize the module even if @types/quill-delta is not available.
// For more detailed typing, this file could be expanded, or a proper @types package used if one exists.

declare module 'quill-delta' {
  class Delta {
    ops: any[]; // Basic representation, can be made more specific
    constructor(ops?: any[] | { ops: any[] });
    insert(arg: any, attributes?: Record<string, any>): Delta;
    delete(length: number): Delta;
    retain(length: number, attributes?: Record<string, any>): Delta;
    concat(other: Delta): Delta;
    chop(): Delta;
    slice(start?: number, end?: number): Delta;
    compose(other: Delta): Delta;
    diff(other: Delta, index?: number | ((index: number, length: number) => boolean)): Delta;
    transform(other: Delta, priority?: boolean): Delta;
    transformPosition(index: number, priority?: boolean): number;
    length(): number;
    // Add other methods or properties if needed for type checking
  }
  export default Delta;
}
